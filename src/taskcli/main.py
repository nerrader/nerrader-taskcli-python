import typer
from taskcli import tasks
from rich.theme import Theme
from rich.console import Console
from rich.table import Table
from typing import Annotated
from typer_extensions import ExtendedTyper
import questionary

CUSTOM_THEME = Theme(
    {"error": "red", "success": "green", "info": "blue", "warning": "yellow"}
)
CONSOLE = Console(theme=CUSTOM_THEME)
print = CONSOLE.print

app = ExtendedTyper()
task_manager = (
    tasks.TasklistManager()
)  # the __init__ auto loads the tasklist and next_id


@app.command("add")
def add_task(
    name: Annotated[list[str], typer.Argument(help="The name of the task")],
    priority: Annotated[
        str, typer.Option("--priority", "-p", help="The priority of the created task")
    ] = "medium",
) -> None:
    """Adds a task to the tasklist with the args being the values of the attributes for the task.

    Raises:
        typer.BadParameter: If the priority provided by the user is not a valid priority, raise this error.
    """
    name = (" ".join(name)).strip()
    results = task_manager.add_task(name, priority=priority)
    print(results)
    display_tasks_table()


@app.command_with_aliases("delete", aliases=["remove", "del", "rm"])
def delete_task(
    task_id: Annotated[
        int, typer.Argument(help="The task id of the task being deleted")
    ],
) -> None:
    """Deletes a task based on the task id given by the user

    Args:
        task_id (int): The task ID of the given task that the user wants to delete.
    """
    results = task_manager.delete_task(task_id)
    print(results)
    display_tasks_table()


@app.command("update")
def update_task(
    task_id: int,
    updated_name: Annotated[
        list[str] | None, typer.Option("--name", "-n", help="The updated name")
    ] = None,
    updated_priority: Annotated[
        str | None, typer.Option("--priority", "-p", help="The updated priority")
    ] = None,
) -> None:
    """Updates a specific task given the task id by the user.

    Args:
        task_id (int): The task ID of the task that the user wants to update.
        updated_name (str|None): The updated name given by the user. Defaults to None.
        updated_priority (str|None): The updated priority given by the user. Defaults to None.

    Raises:
        typer.BadParameter: The user did not enter a valid priority
        typer.BadParameter (x2): The user did not have a name nor priority attribute to update.
    """
    raw_updated_contents = {
        "name": (" ".join(updated_name)) if updated_name else None,
        "priority": updated_priority,
    }
    # it will validate it
    results = task_manager.update_task(task_id, raw_updated_contents)
    print(results)
    display_tasks_table()


@app.command("mark")
def mark_task(
    task_id: Annotated[
        int, typer.Argument(help="The task id being marked as the upadted status")
    ],
    updated_status: Annotated[
        str, typer.Argument(help="The updated status of the task ID given by the user")
    ],
) -> None:
    if updated_status not in tasks.Task.VALID_STATUSES:
        raise typer.BadParameter(
            f"Invalid status: '{updated_status}'. Must be one of {tasks.Task.VALID_STATUSES}"
        )
    results = task_manager.mark_task(task_id, updated_status)
    print(results)
    display_tasks_table()


def display_tasks_table() -> None:
    """This is an internal CLI Command to display the rich table based off the tasklist"""
    if len(task_manager.tasklist) == 0:
        print("There is nothing in the tasklist...", style="info")
    tasks_table = Table(title="Tasklist", show_lines=True)
    tasks_table.add_column("ID")
    tasks_table.add_column("Name")
    tasks_table.add_column("Status")
    tasks_table.add_column("Priority")

    priority_colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "urgent": "bold red",
    }

    for task in task_manager.tasklist:
        task_priority_color = priority_colors[
            task.priority
        ]  # if show_priority_colors is enabled in settings
        tasks_table.add_row(
            str(task.id),
            task.name,
            task.status,
            f"[{task_priority_color}]{task.priority}[/{task_priority_color}]",
        )
    print("")
    print(tasks_table)
    print("")
    # newlines to make it look better


@app.command_with_aliases("list", aliases=["ls", "view"])
def list_tasks() -> None:
    """The actual CLI Command to list the rich table tasklist"""
    display_tasks_table()


@app.command("clear")
def clear_tasks() -> None:
    """Asks a confirmation prompt first, then if they confirm, clear the tasklist"""
    confirm_clear: bool = questionary.confirm(
        "Are you sure you want to clear the entire tasklist?"
    ).ask()
    if not confirm_clear:
        return
    results = task_manager.clear_tasklist()
    print(results)


def main():
    app()


if __name__ == "__main__":
    main()

# crud operations, saving and loading
