import typer
from taskcli import tasks
from rich.theme import Theme
from rich.console import Console
from rich.table import Table
from typing import Annotated
from typer_extensions import ExtendedTyper
import questionary
from taskcli import storage
from taskcli import config
from dataclasses import dataclass

CUSTOM_THEME = Theme(
    {"error": "red", "success": "green", "info": "blue", "warning": "yellow"}
)
CONSOLE = Console(theme=CUSTOM_THEME)
print = CONSOLE.print

app = ExtendedTyper()


@dataclass
class ContextObject:
    task_manager: tasks.TasklistManager
    config: config.Config


@app.command("add")
def add_task(
    context: typer.Context,
    name: Annotated[list[str], typer.Argument(help="The name of the task")],
    priority: Annotated[
        str, typer.Option("--priority", "-p", help="The priority of the created task")
    ] = None,  # let the add_task() get the default priority later
    status: Annotated[
        str, typer.Option("--status", "-s", help="The status of the created task")
    ] = None,  # the __init__ in task class will automatically add a default value
) -> None:
    """Adds a task to the tasklist with the args being the values of the attributes for the task.

    Raises:
        typer.BadParameter: If the priority provided by the user is not a valid priority, raise this error.
    """
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    name = (" ".join(name)).strip()
    results = state.task_manager.add_task(name, priority, status)
    print(results)
    display_tasks_table(context)


@app.command_with_aliases("delete", aliases=["remove", "del", "rm"])
def delete_task(
    context: typer.Context,
    task_id: Annotated[
        int, typer.Argument(help="The task id of the task being deleted")
    ],
) -> None:
    """Deletes a task based on the task id given by the user

    Args:
        task_id (int): The task ID of the given task that the user wants to delete.
    """
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    confirm_delete = (
        questionary.confirm(f"Are you sure you want to delete task ID {task_id}")
        .skip_if(not state.config.behaviour_settings.confirm_on_delete, default=True)
        .ask()
    )
    if not confirm_delete:
        print("Task deletion cancelled")
        return

    results = state.task_manager.delete_task(task_id)
    print(results)
    display_tasks_table(context)


@app.command("update")
def update_task(
    context: typer.Context,
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
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    raw_updated_contents = {
        "name": (" ".join(updated_name)) if updated_name else None,
        "priority": updated_priority,
    }
    # it will validate it
    results = state.task_manager.update_task(task_id, raw_updated_contents)
    print(results)
    display_tasks_table(context)


@app.command("mark")
def mark_task(
    context: typer.Context,
    task_id: Annotated[
        int, typer.Argument(help="The task id being marked as the upadted status")
    ],
    updated_status: Annotated[
        str, typer.Argument(help="The updated status of the task ID given by the user")
    ],
) -> None:
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    if updated_status not in tasks.Task.VALID_STATUSES:
        raise typer.BadParameter(
            f"Invalid status: '{updated_status}'. Must be one of {tasks.Task.VALID_STATUSES}"
        )
    results = state.task_manager.mark_task(task_id, updated_status)
    print(results)
    display_tasks_table(context)


def display_tasks_table(context: typer.Context) -> None:
    """This is an internal CLI Command to display the rich table based off the tasklist"""
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    if len(state.task_manager.tasklist) == 0:
        print("There is nothing in the tasklist...", style="info")
    tasks_table = Table(
        title="Tasklist", show_lines=state.config.behaviour_settings.show_table_lines
    )

    for column_name in state.config.visible_columns:
        tasks_table.add_column(column_name)

    priority_colors = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "urgent": "bold red",
    }

    for task in state.task_manager.tasklist:
        # this is for auto clear done tasks setting, put it somewhere else
        if (
            state.config.behaviour_settings.auto_clear_done_tasks
            and task.status == "done"
        ):
            state.task_manager.delete_task(task.id)
            continue

        if state.config.behaviour_settings.auto_clear_done_tasks:
            state.task_manager.tasklist = [
                task for task in state.task_manager.tasklist if task.status != "done"
            ]

            # this is for the show priority colors setting
        task_priority_color = "white"
        if state.config.behaviour_settings.show_priority_colors:
            task_priority_color = priority_colors[task.priority]

        visible_task_contents: list[str] = []
        task_attribute_map = {
            "ID": str(task.id),
            "Name": task.name,
            "Status": task.status,
            "Priority": f"[{task_priority_color}]{task.priority}[/{task_priority_color}]",
        }
        for column_name in state.config.visible_columns:
            visible_task_contents.append(task_attribute_map[column_name])
        tasks_table.add_row(*visible_task_contents)

    print("")
    print(tasks_table)
    print("")
    # newlines to make it look better


@app.command_with_aliases("list", aliases=["ls", "view"])
def list_tasks(context: typer.Context) -> None:
    """The actual CLI Command to list the rich table tasklist"""
    display_tasks_table(context)


@app.command("clear")
def clear_tasks(context: typer.Context) -> None:
    """Asks a confirmation prompt first, then if they confirm, clear the tasklist"""
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    confirm_clear: bool = (
        questionary.confirm("Are you sure you want to clear the entire tasklist?")
        .skip_if(not state.config.behaviour_settings.confirm_on_clear, True)
        .ask()
    )
    if not confirm_clear:
        return
    results = state.task_manager.clear_tasklist()
    print(results)


@app.command("config")
def config_cli(context: typer.Context):
    state: ContextObject = context.obj

    state.config.main_configuration_ui()


@app.callback()
def initialize(context: typer.Context):
    """basically this is the first thing that runs when app() is called
    we first check storage to generate the files and stuff if they dont exist, then
    we create a context.obj to store the variables in

    Args:
        context (typer.Context): Context object used by typer. You must use context.obj to store persistent values.
    """
    storage.check_storage()
    context.obj = ContextObject(tasks.TasklistManager(), config.Config())


def main():
    app()


if __name__ == "__main__":
    main()

# crud operations, saving and loading
