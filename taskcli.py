import argparse
import json
from pathlib import Path
from os import getenv, makedirs
import rich
from rich.console import Console
from rich.theme import Theme
import questionary


custom_color_themes = Theme(
    {
        "success": "green",
        "error": "bold red",
        "info": "cyan",
        "warning": "yellow",
        "dim": "dim bright_black",
    }
)
console = Console(theme=custom_color_themes)
print = console.print  # override the original print with the better one


def format_whitespace(data: list[str] | str | None) -> str | None:
    if data is None:
        return None
    elif isinstance(data, list):
        data = " ".join(data)
    return " ".join(data.split())


print("")  # more aesthetically pleasing
default_config = {
    "show_columns": ["ID", "Name", "Status", "Priority"],
    "table_show_lines": True,
    "show_priority_colors": True,
    "default_priority": "medium",
    "auto_clear_done_tasks": False,
    "confirm_on_clear": True,
    "confirm_on_delete": False,
    # "sort_by": "id_asc", add this later
}
config = default_config.copy()
save_filepath = Path.home() / ".taskcli"
tasks_file = save_filepath / "tasks.json"
config_file = save_filepath / "config.json"
makedirs(save_filepath, exist_ok=True)
try:
    with open(tasks_file, "r") as f:
        tasklist = json.load(f)
    with open(config_file, "r") as f:
        config = json.load(f)
except Exception as error:
    if isinstance(error, FileNotFoundError):
        with open(tasks_file, "w") as f:
            json.dump([], f, indent=4)
        with open(config_file, "w") as f:
            json.dump(default_config, f, indent=4)
    tasklist = []


class Task:
    valid_statuses: tuple[str] = ("todo", "done")
    valid_priorities: tuple[str] = ("low", "medium", "high", "urgent")

    def __init__(self, name, priority):
        self.name = name
        self._id = max((task["id"] for task in tasklist), default=0) + 1
        self.status = "todo"
        self.priority = priority

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "id": self._id,
            "status": self.status,
            "priority": self.priority,
        }

    @property
    def id(self) -> int:
        return self._id


parser = argparse.ArgumentParser(description="My Taskcli")

subparsers = parser.add_subparsers(dest="command", help="Different types of commands")

add_parser = subparsers.add_parser("add", help="adds a task")
add_parser.add_argument(
    "-n", "--name", nargs="+", help="The name of the task added", required=True
)
add_parser.add_argument(
    "-p",
    "--priority",
    help="The priority level",
    choices=Task.valid_priorities,
    type=str.lower,
    default=config["default_priority"],
)

delete_parser = subparsers.add_parser(
    "delete", help="deletes a task", aliases=["remove", "del", "rm"]
)
delete_parser.add_argument("id", help="The ID of the task deleted", type=int)

update_parser = subparsers.add_parser(
    "update", help="updates a task's name/description"
)
update_parser.add_argument("id", help="The ID of the task updated", type=int)
update_parser.add_argument("-n", "--name", help="the updated name", nargs="+")
update_parser.add_argument("-p", "--priority", help="the updated priority")

mark_parser = subparsers.add_parser("mark", help="marks a task as todo/done")
mark_parser.add_argument("id", help="The ID of the task being updated", type=int)
mark_parser.add_argument(
    "status",
    help="Mark a task as todo/done",
    choices=Task.valid_statuses,
    type=str.lower,
)

list_parser = subparsers.add_parser("list", help="lists the tasklist", aliases=["view"])

clear_parser = subparsers.add_parser("clear", help="clears the tasklist")
clear_parser.add_argument(
    "-y",
    "--yes",
    help="Bypasses the confirmation prompt on clear",
    action="store_true",
    dest="yes",
)

configure_parser = subparsers.add_parser(
    "configure", help="Configure your settings", aliases=["config", "settings"]
)


def find_task(target_id) -> dict:
    return next((task for task in tasklist if task["id"] == target_id), None)


def list_tasks() -> None:
    if len(tasklist) == 0:
        print("There are no tasks in the tasklist.", style="info")
        return
    priority_color = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "urgent": "bold red",
    }
    table = rich.table.Table(
        title="Tasklist",
        title_justify="left",
        show_lines=config["table_show_lines"],
        title_style="info",
    )
    table_columns = config["show_columns"]
    for column in table_columns:
        table.add_column(column)
    for task in tasklist:
        task_data = []
        for column in table_columns:
            if column.lower() == "priority" and config["show_priority_colors"]:
                task_data.append(
                    f"[{priority_color[task['priority']]}]{task['priority']}[/{priority_color[task['priority']]}]"
                )
            else:
                task_data.append(str(task[column.lower()]))
        table.add_row(*task_data)
    console.print(table)


def add_task(task_name: str, task_priority) -> None:
    new_task = Task(task_name, task_priority).to_dict()
    tasklist.append(new_task)
    print(f"Successfully added new task: {task_name}", style="success")


def del_task(target_id: int) -> None:
    if config["confirm_on_delete"]:
        confirm = questionary.confirm(
            f"Are you sure you want to delete task ID {target_id}"
        ).ask()
    else:
        confirm = True
    target_task = find_task(target_id)
    if target_task and confirm:
        tasklist.remove(target_task)
        print(f"Successfully removed task with ID {target_id}", style="success")
        list_tasks()
    else:
        print(f"Couldn't find a task with ID {target_id}", style="error")


def update_task(args) -> None:
    target_id = args.id
    target_task = find_task(target_id)
    update_contents = {
        "name": format_whitespace(args.name),
        "priority": format_whitespace(args.priority),
    }
    if target_task is None:
        print(f"Could not find a task with ID {target_id}", style="error")
    elif any(update_contents.values()) is None:
        print("You did not provide anything to update", style="error")
    else:
        for key, value in update_contents.items():
            if value is not None:
                target_task[key] = value
        else:
            print("Everything is updated!", style="success")
            list_tasks()


def mark_task(target_id, updated_status) -> None:
    target_task = find_task(target_id)
    if target_task:
        target_task["status"] = updated_status
        print(
            f"Successfully marked task with ID {target_id} as {updated_status}",
            style="success",
        )
        if updated_status == "done" and config["auto_clear_done_tasks"]:
            tasklist.remove(target_task)
        list_tasks()
    else:
        print(f"Could not find a task with ID {target_id}", style="error")


def clear_tasks() -> None:
    if config["confirm_on_clear"] and not args.yes:
        confirm = questionary.confirm(
            "Are you sure you want to clear your tasklist?"
        ).ask()
    else:
        confirm = True
    if confirm:
        tasklist.clear()
        print("Successfully cleared tasklist", style="success")
    else:
        print("Clear cancelled.", style="info")


def configure_settings(config) -> None:  # saves it directly in the function
    def configure_behaviour_settings() -> dict:
        while True:
            behaviour_settings_chioces = (
                questionary.Choice(
                    title=f"Show Priority Colors [{config['show_priority_colors']}]",
                    value="show_priority_colors",
                ),
                questionary.Choice(
                    title=f"Table Show Lines [{config['table_show_lines']}]",
                    value="table_show_lines",
                ),
                questionary.Choice(
                    title=f"Auto Clear Done Tasks [{config['auto_clear_done_tasks']}]",
                    value="auto_clear_done_tasks",
                ),
                questionary.Choice(
                    title=f"Confirm on Clear [{config['confirm_on_clear']}]",
                    value="confirm_on_clear",
                ),
                questionary.Choice(
                    title=f"Confirm on Delete [{config['confirm_on_delete']}]",
                    value="confirm_on_delete",
                ),
                questionary.Choice(title="Go Back", value="back"),
            )

            selection = questionary.select(
                "Behaviour Settings",
                choices=behaviour_settings_chioces,
                default=None,
            ).ask()
            if selection == "back" or selection is None:
                break
            else:
                config[selection] = not config[selection]
        return config

    def configure_toggled_columns() -> dict:
        config["show_columns"] = questionary.checkbox(
            "Toggle Visibility", choices=("ID", "Name", "Status", "Priority")
        ).ask()
        return config

    def configure_default_priority() -> dict:
        config["default_priority"] = questionary.select(
            "Default Priority", choices=("low", "medium", "high", "urgent")
        ).ask()
        return config

    def save_config(new_config) -> None:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=4)
            print("Successfully configured settings!", style="success")
            return

    def main() -> None:
        while True:
            nonlocal config
            choice = questionary.select(
                "Settings Menu",
                choices=(
                    "Toggle Columns",
                    "Behaviour Settings",
                    "Configure Default Priority",
                    questionary.Separator(""),
                    "Set Default",
                    "Exit and Save",
                    "Cancel",
                ),
            ).ask()
            match choice:
                case "Toggle Columns":
                    config = configure_toggled_columns()
                case "Configure Default Priority":
                    config = configure_default_priority()
                case "Behaviour Settings":
                    config = configure_behaviour_settings()
                case "Set Defaults":
                    config.clear()
                    config.update(default_config)
                case "Cancel":
                    cancel_confirm = questionary.confirm(
                        "Are you sure? Your settings will not be saved."
                    ).ask()
                    if cancel_confirm:
                        break
                case "Exit and Save":
                    try:
                        save_config(config)
                    except Exception as error:
                        print(error, style="error")
                    break
        return

    main()


args = parser.parse_args()
match args.command:
    case "add":
        args.name = format_whitespace(args.name)
        add_task(args.name, args.priority)
        list_tasks()
    case "delete" | "del" | "remove" | "rm":
        del_task(args.id)
    case "update":
        update_task(args)
    case "mark":
        mark_task(args.id, args.status)
    case "list" | "view":
        list_tasks()
    case "clear":
        clear_tasks()
    case "config" | "configure" | "settings":
        configure_settings(config)
    case _:
        print("what happened")


with open(tasks_file, "w", encoding="utf-8") as f:
    json.dump(tasklist, f, indent=4)


print("")  # to also make it look better
# Features:
# [x] add, delete, update, list tasks
# [x] priority levels, colored text
# duedates (ex: --due friday, --due 3-13-2027, --due today, --due tomorrow)
# list task today (filters pretty much)
# task created_at, and completed_at, so we can create a report to see how productive you were
# be able to sort tasks based off something, status, time added or completed, etc
# [x] settings or config
# task undo/redo should exist
# [x] be able to access this taskcli anywhere in the cmd
