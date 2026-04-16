import typer
from taskcli import tasks
from rich.theme import Theme
from rich.console import Console
from rich.table import Table
from typing import Annotated, Optional
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
    verbose_mode: bool


@app.command("add")
def add_task(
    context: typer.Context,
    name: Annotated[list[str], typer.Argument(help="The name of the task")],
    priority: Annotated[
        Optional[str],
        typer.Option("--priority", "-p", help="The priority of the created task"),
    ] = None,  # let the add_task() get the default priority later
    status: Annotated[
        Optional[str],
        typer.Option("--status", "-s", help="The status of the created task"),
    ] = None,  # the __init__ in task class will automatically add a default value
) -> None:
    """Adds a task to the tasklist with the args being the values of the attributes for the task.

    Raises:
        typer.BadParameter: If the priority provided by the user is not a valid priority, raise this error.
    """
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    # to override the old list[str] so mypys happy
    joined_name: str = (" ".join(name)).strip()
    results = state.task_manager.add_task(joined_name, priority, status)
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
        .skip_if(
            not state.config.behaviour_settings.require_delete_confirmation,
            default=True,
        )
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
        Optional[list[str]], typer.Option("--name", "-n", help="The updated name")
    ] = None,
    updated_priority: Annotated[
        Optional[str],
        typer.Option("--priority", "-p", help="The updated priority"),
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

    joined_updated_name: str | None = " ".join(updated_name) if updated_name else None
    raw_updated_contents = {
        "name": joined_updated_name,
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

    priority_colors: dict[str, str] = {
        "low": "green",
        "medium": "yellow",
        "high": "red",
        "urgent": "bold red3",
    }
    status_colors: dict[str, str] = {
        "on-hold": "dim",
        "todo": "white",
        "doing": "bold blue",
        "done": "green4",
    }
    for task in state.task_manager.tasklist:
        # this is for the show priority colors setting
        task_priority_color: str = "white"
        if state.config.behaviour_settings.show_priority_colors:
            task_priority_color = priority_colors[task.priority]

        # for the show status colors setting
        task_status_color = "white"
        if state.config.behaviour_settings.show_status_colors:
            task_status_color = status_colors[task.status]

        visible_task_contents: list[str] = []

        task_attribute_map = {
            "ID": str(task.id),
            "Name": task.name,
            "Status": f"[{task_status_color}]{task.status}[/]",
            "Priority": f"[{task_priority_color}]{task.priority}[/]",
        }

        for column_name in state.config.visible_columns:
            visible_task_contents.append(task_attribute_map[column_name])
        tasks_table.add_row(*visible_task_contents)

    print("\n", tasks_table, "\n")
    # newlines to make it look better


@app.command_with_aliases("list", aliases=["ls", "view"])
def list_tasks(context: typer.Context) -> None:
    """The actual CLI Command to list the rich table tasklist"""
    display_tasks_table(context)


@app.command("clear")
def clear_tasks(
    context: typer.Context,
    confirm: Annotated[
        Optional[bool],
        typer.Option("--confirm", "-c", help="Skips the confirmation prompt"),
    ] = False,
) -> None:
    """Asks a confirmation prompt first, then if they confirm, clear the tasklist"""
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    confirm_clear: bool = (
        questionary.confirm("Are you sure you want to clear the entire tasklist?")
        .skip_if(
            not state.config.behaviour_settings.require_clear_confirmation or confirm,
            True,
        )
        .ask()
    )
    if not confirm_clear:
        return
    results = state.task_manager.clear_tasklist()
    print(results)


@app.command("config")
def config_cli(context: typer.Context) -> None:
    state: ContextObject = context.obj

    state.config.main_configuration_ui()


@app.callback()
def initialize(
    context: typer.Context,
    verbose: Annotated[
        Optional[bool],
        typer.Option(
            "-v", "--verbose", help="This flag enables verbose mode", expose_value=False
        ),
    ] = False,
) -> None:
    # basically this is the first thing that runs when app() is called
    # we first check storage to generate the files and stuff if they dont exist, then
    # we create a context.obj to store the variables in

    # Args:
    #     context (typer.Context): Context object used by typer. You must use context.obj to store persistent values.
    #
    storage.check_storage()
    task_manager: tasks.TasklistManager = tasks.TasklistManager()
    context_config: config.Config = config.Config()
    final_verbose_mode: bool = context_config.behaviour_settings.verbose_mode or verbose

    # where else am i supposed to put it
    if context_config.behaviour_settings.auto_clear_done_tasks:
        task_manager.tasklist = [
            task for task in task_manager.tasklist if task.status != "done"
        ]
        task_manager.save_tasks()

    context.obj = ContextObject(task_manager, context_config, final_verbose_mode)


def main():
    try:
        app()
    except Exception as e:
        print(str(e))


if __name__ == "__main__":
    main()

# add duedates and make verbose mode work and also list filtering when listing tasks (release taskcli revamp after)
# make it so that you can change between tasklists (branches pretty much)
# add tags and task groups
# undo redo
