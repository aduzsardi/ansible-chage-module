#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Copyright (C) 2022 Alexandru Duzsarid <alex[at]ilogicgroup[dot]org>

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


ANSIBLE_METADATA = {'metadata_version': '1.0',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
module: chage
short_description: a very minimal module to query/change user account expiration date on Linux
description:
    - query and change user account expiration on Linux
    - calls chage command to make changes
    - returns user expiration date
    - for detailed information on shadow file & chage command see:
        - /usr/include/shadow.h
        - man chage
        - pydoc spwd
    - dates can be in the form YYYY-MM-DD , days since 1970/1/1 or -1 which means no expiration

notes: []
version_added: null
author:
    - 'Alex Duzsardi (@aduzsardi)'
options:
    user:
        required: true
        description:
          - user name
        aliases: [name, username]

    expire_date:
        required: false
        default: None
        description:
          - set the date in format YYYY-MM-DD until account expires
          - chage option = -E, --expiredate
          - remove the field by passing value of -1
"""

EXAMPLES = """
# remove an account expiration date.
- chage: user=john expire_date=-1

# display user account expiration date
- chage: user=john
  register: user
- debug: msg={{user.info.expire_date}}
"""

from datetime import date, timedelta
import re
from ansible.module_utils.basic import AnsibleModule

try:
    import spwd
    HAVE_SPWD = True
except ImportError:
    HAVE_SPWD = False


pattern = re.compile('[0-9]{4}-[0-9]{2}-[0-9]{2}')

def _expire_date_converter(fmt):
    if pattern.fullmatch(str(fmt)):
        return (str(fmt), str(fmt))
    elif str(fmt).isdigit and int(fmt) > 0:
        isodate = timedelta(days=int(fmt)) + date(1970, 1, 1)
        return (isodate.isoformat(), isodate.isoformat())
    elif str(fmt).lower() in ['-1', '', 'never', -1]:
        return ('Never', -1)
    return

def _human_shadow(shadow_dict):
    shadow_dict['expire_date'] = _expire_date_converter(
        shadow_dict['expire_date'])[0]
    return shadow_dict


def main():
    module = AnsibleModule(
        argument_spec = dict(
            user = dict(type='str', required=True,  aliases=['name','username']),
            expire_date = dict(type='str', required=False, default=None),
        ),
        supports_check_mode = True
    )

    user = module.params['user']

    if HAVE_SPWD:
        try:
            current_shadow = spwd.getspnam(user)
            current_shadow = dict(
                user=current_shadow[0], 
                expire_date=current_shadow[7],
                )
            current_shadow = _human_shadow(current_shadow)
        except PermissionError as err:
            message = "Unable to open /etc/shadow, error(%s): %s" % (err.errno, err.strerror)
            module.fail_json(msg=message)
        except KeyError as err:
            message = "Username not found, error(%s): %s" % (err.errno, err.strerror)
            module.fail_json(msg=message)
        
    chage_flags = dict(
        expire_date = '--expiredate',
    )

    # Start building 'chage' command to make changes.
    cmd = []

    # build return value in case command is successful
    new_shadow = current_shadow

    for param_name, flag_name in chage_flags.items():
        desired_value = module.params[param_name]
        if desired_value is not None:
            if param_name in ['expire_date']:
                if _expire_date_converter(desired_value):
                    desired_value, desired_cmd_value = _expire_date_converter(desired_value)

            if desired_value != current_shadow[param_name]:
                cmd.append(flag_name)
                cmd.append(desired_cmd_value)
                new_shadow[param_name] = desired_value


    # were any changes needed ?
    if cmd.__len__() == 0:
        # no changes needed
        module.exit_json(info=current_shadow, changed=False)

    if module.check_mode:
        module.exit_json(info=_human_shadow(new_shadow), changed=True)

    # complete command and run it
    cmd.insert(0, module.get_bin_path('chage', required=True))
    cmd.append(user)
    (rc, out, err) = module.run_command(cmd)

    # fail if command didn't work
    if rc is not None and rc != 0:
        module.fail_json(msg=err, rc=rc)

    # command succeeded, so return the updated shadow entry
    module.exit_json(info=_human_shadow(new_shadow), changed=True)
main()
