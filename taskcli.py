import argparse
import json
from pathlib import Path
from os import getenv, makedirs
from rich import print
from rich.prompt import Prompt

input = Prompt.ask  # replace input() with prompt.ask()

tasklist = []
save_filepath = Path(getenv("APPDATA")) / "taskcli"


makedirs(save_filepath, exist_ok=True)
save_filepath = save_filepath / "tasks.json"
try:
    with open(save_filepath, "r") as f:
        tasklist = json.load(f)
except FileNotFoundError:
    tasklist = []


class Task:
    valid_statuses: tuple[str] = ("todo", "done")

    def __init__(self, name):
        self.name = name
        self._id = max((task["id"] for task in tasklist), default=0) + 1
        self.status = "todo"

    def to_dict(self) -> dict:
        return {"name": self.name, "id": self.id, "status": self.status}

    @property
    def id(self) -> int:
        return self._id


parser = argparse.ArgumentParser(description="My Taskcli")

subparsers = parser.add_subparsers(dest="command", help="Different types of commands")

add_parser = subparsers.add_parser("add", help="adds a task")
add_parser.add_argument("name", nargs="+", help="The name of the task added")

delete_parser = subparsers.add_parser("delete", help="deletes a task")
delete_parser.add_argument(
    "id",
    help="The ID of the task deleted",
    type=int,
)

update_parser = subparsers.add_parser(
    "update", help="updates a task's name/description"
)
update_parser.add_argument("id", help="The ID of the task updated", type=int)
update_parser.add_argument("-n", "--name", help="the updated name", nargs="+")

mark_parser = subparsers.add_parser("mark", help="marks a task as todo/done")
mark_parser.add_argument("id", help="The ID of the task being updated", type=int)
mark_parser.add_argument(
    "status",
    help="Mark a task as todo/done",
    choices=Task.valid_statuses,
    type=str.lower,
)

list_parser = subparsers.add_parser("list", help="lists the tasklist")

clear_parser = subparsers.add_parser("clear", help="clears the tasklist")


def find_task(target_id) -> dict:
    return next((task for task in tasklist if task["id"] == target_id), None)


def log_error_message(msg, code="ERROR"):
    print(f"[bold red]{code}: [/bold red][red]{msg}[/red]")


def log_success_message(msg):
    print(f"[green]{msg}[/green]")


def format_whitespace(data: list[str] | str | None) -> str | None:
    if data is None:
        return None
    elif isinstance(data, list):
        data = " ".join(data)
    return " ".join(data.split())


def list_tasks() -> None:
    print("")  # newline to make it look better
    print("[bold yellow]Tasklist:[/bold yellow]")
    for task in tasklist:
        print(f"- {task['name']} | {task['status']} [dim][ID: {task['id']}][/dim]")


def add_task(task_name: str) -> None:
    new_task = Task(task_name).to_dict()
    tasklist.append(new_task)
    log_success_message(f"Added new Task: {task_name}")


def del_task(target_id: int) -> None:
    target_task = find_task(target_id)
    if target_task:
        tasklist.remove(target_task)
        log_success_message(f"Successfully removed task with ID {target_id}")
        list_tasks()
    else:
        log_error_message(f"Couldn't find a task with ID {target_id}")


def update_task(args) -> None:
    target_id = args.id
    target_task = find_task(target_id)
    update_contents = {"name": format_whitespace(args.name)}
    if target_task is None:
        log_error_message(f"Could not find a task with ID {target_id}")
    elif any(update_contents.values()) is None:
        log_error_message("You did not provide anything to update")
    else:
        for key, value in update_contents.items():
            if value is not None:
                target_task[key] = value
        else:
            log_success_message("Everything is updated!")
            list_tasks()


def mark_task(target_id, updated_status) -> None:
    target_task = find_task(target_id)
    if target_task:
        target_task["status"] = updated_status
        log_success_message(
            f"Successfully marked task with ID {target_id} as {updated_status}"
        )
        list_tasks()
    else:
        log_error_message(f"Could not find a task with ID {target_id}")


def clear_tasks() -> None:
    confirm = (
        input("Are you sure you want to clear your tasklist? [yes/no] ")
        .lower()
        .strip()
        .replace(" ", "")
    )
    if confirm in ["yes", "y"]:
        tasklist.clear()
        print("[yellow]Cleared tasklistp[/yellow]")
    else:
        print("[yellow]Clear cancelled.[/yellow]")


args = parser.parse_args()

match args.command:
    case "add":
        args.name = format_whitespace(args.name)
        add_task(args.name)
        list_tasks()
    case "delete":
        del_task(args.id)
    case "update":
        update_task(args)
    case "mark":
        mark_task(args.id, args.status)
    case "list":
        list_tasks()
    case "clear":
        clear_tasks()


with open(save_filepath, "w", encoding="utf-8") as f:
    json.dump(tasklist, f, indent=4)

print("")  # to also make it look better
# Features:
# [x] add, delete, update, list tasks
# priority levels, colored text
# duedates (ex: --due friday, --due 3-13-2027, --due today, --due tomorrow)
# list task today (filters pretty much)
# task created_at, and completed_at, so we can create a report to see how productive you were
# be able to sort tasks based off something, status, time added or completed, etc
# settings or config
# task undo/redo should exist
# [x] be able to access this taskcli anywhere in the cmd
