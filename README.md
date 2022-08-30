# Ansible Module: chage

A very minimal module to query/change user account expiration date on Linux

Inspired from [
John Buxton's](https://github.com/lqueryvg/ansible-role-chage) `chage` [module](https://github.com/lqueryvg/ansible-role-chage) , but changed most of the code for my needs and to learn something along the way.

## Features

- query and change user account expiration on Linux
- returns user expiration date

## Examples

```yaml
# remove an account expiration date.
- chage: user=john expire_date=-1

# display user account expiration date
- chage: user=john
  register: user
- debug: msg={{user.info.expire_date}}
```

## Options

Most of the option names follow the fields documented
in `/usr/include/shadow.h` and `pydoc spwd`.

See also `man chage`.

| argument  | alias      | required | default | comments
|:----------|:-----------|:---------|:--------|:-------------|
| user      |            | yes      |         | user name
| expire_date |          | no       | None    | chage -E, --expiredate <br>days since 1970-01-01 until account expires or date in format YYYY-MM-DD , `-1` to clear the expiration date


## Requirements

- `chage` command
- `/etc/shadow` file (read pwconv man page if `/etc/shadow` does not exist)
- root access (to read `/etc/shadow` file)

## License

Apache 2.0

## Author Information

[Alex Duzsardi](https://github.com/aduzsardi)
