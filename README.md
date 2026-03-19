This is a taskcli made in python by me

how to install:

1. download/install uv (https://astral.sh/uv)
2. run `uv tool install git+https://github.com/nerrader/nerrader-taskcli-python`
3. type taskcli {and another command here} to use it

commands

- add (ex: taskcli add -n (--name) {name} -p (--priority: optional) {priority})
- delete/remove/del/rm (ex: taskcli delete {id})
- update (ex: taskcli update {id} -n (--name, updated name), -p (--priority, updated priority) (pick either name/priority or both))
- mark (ex: taskcli mark {id} {todo/done})
- list -p (--name, optional: filters based off priority) -s (--status, optional: filters based off status)
- clear -y (--yes, optional: bypasses clear confirm)
- configure/config/settings (no args)

notes:

- this application will store files in (your home folder/taskcli), deleting them will reset your taskcli/config (depending on what you deleted)
