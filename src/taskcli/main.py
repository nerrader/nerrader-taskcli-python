from dataclasses import dataclass
import sys  # we import sys for stderr for loguru specifically
from typing import Annotated, Optional

from loguru import logger  # for logging
import questionary  # for cli prompts (confirm/selection/checkbox)

# rich things, for themes colors and tables
from rich.theme import Theme
from rich.console import Console
from rich.table import Table

# typer things
import typer

# other taskcli files, local to project
from taskcli import tasks
from taskcli import storage
from taskcli import config

CUSTOM_THEME = Theme(
    {"error": "red", "success": "green", "info": "blue", "warning": "yellow"}
)
CONSOLE = Console(theme=CUSTOM_THEME)
print = CONSOLE.print
app = typer.Typer()


@dataclass
class ContextObject:
    task_manager: tasks.TasklistManager
    config: config.Config
    verbose_mode: bool


@logger.catch(level="ERROR")
def handleResults(result: tasks.ResultManager) -> None:
    """Logs and prints the results, automatically determines level depending on the success value.

    Args:
        result (tasks.ResultManager): The results given by a function from tasks.py being handled.

    Raises:
        ValueError: If results were empty or if no results were given, raise this.
    """
    if not result:
        raise ValueError("No results found in the handleResults() function.")
    print(result)

    log = logger.bind(data=result.data)
    if result.success:
        log.success(result.message)
    else:
        log.error(result.message)


@logger.catch(level="ERROR")
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
    logger.info(
        "User invoked add command",
    )
    logger.debug(
        "command_params",
        command_params={"name": name, "priority": priority, "status": status},
    )

    # literally just for the autocomplete really
    state: ContextObject = context.obj

    # to override the old list[str] so mypys happy
    joined_name: str = (" ".join(name)).strip()

    # the add_task function will deal with the missing values themselves
    results = state.task_manager.add_task(joined_name, priority, status)
    handleResults(results)
    display_tasks_table(context)


@logger.catch(level="ERROR")
@app.command("delete")
@app.command("remove")
@app.command("del")
@app.command("rm")
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
    logger.info("User invoked 'delete' command")
    logger.debug("delete command params", command_params={"task_id": task_id})
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
    handleResults(results)
    display_tasks_table(context)


@logger.catch(level="ERROR")
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
        updated_name (Optional[str]): The updated name given by the user. Defaults to None.
        updated_priority (Optional[str]): The updated priority given by the user. Defaults to None.
    """
    logger.info(
        "User invoked 'update' command",
    )
    logger.debug(
        "update command params",
        command_params={
            "task_id": task_id,
            "updated_name": updated_name,
            "updated_priority": updated_priority,
        },
    )
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    joined_updated_name: str | None = " ".join(updated_name) if updated_name else None
    raw_updated_contents = {
        "name": joined_updated_name,
        "priority": updated_priority,
    }

    results = state.task_manager.update_task(task_id, raw_updated_contents)
    handleResults(results)
    display_tasks_table(context)


@logger.catch(level="ERROR")
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
    logger.info("User invoked 'mark' command")
    logger.debug(
        "mark command params",
        command_params={
            "task_id": task_id,
            "updated_status": updated_status,
        },
    )
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    if updated_status not in tasks.Task.VALID_STATUSES:
        raise typer.BadParameter(
            f"Invalid status: '{updated_status}'. Must be one of {tasks.Task.VALID_STATUSES}"
        )
    results = state.task_manager.mark_task(task_id, updated_status)
    handleResults(results)
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

    # where else am i supposed to put it
    if state.config.behaviour_settings.auto_clear_done_tasks:
        state.task_manager.tasklist = [
            task for task in state.task_manager.tasklist if task.status != "done"
        ]
        state.task_manager.save_tasks()

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


@logger.catch(level="ERROR")
@app.command("list")
@app.command("view")
@app.command("ls")
def list_tasks(context: typer.Context) -> None:
    logger.info("User invoked 'list' command")
    """The actual CLI Command to list the rich table tasklist"""
    display_tasks_table(context)


@logger.catch(level="ERROR")
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
    logger.info("User invoked 'clear' command")
    logger.debug("clear command params", command_params={"clear_confirm": confirm})
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
        logger.info("Cancelled clearing of tasklist")
        return
    results = state.task_manager.clear_tasklist()
    handleResults(results)


@app.command("config")
def config_cli(context: typer.Context) -> None:
    logger.info("User invoked 'config' command")

    state: ContextObject = context.obj
    state.config.main_configuration_ui()


@app.command("reset")
def reset_files():
    logger.info("User invoked 'reset' command")
    reset_confirm = questionary.confirm(
        "Are you sure you want to reset all your tasks and configs? NOTE: This won't reset app logs."
    ).ask()

    if reset_confirm:
        storage.reset_files()
        print("Successfully reset files!", style="success")
        logger.success("Successfully reset appdata files!")


@app.callback()
def initialize(
    context: typer.Context,
    verbose: Annotated[
        Optional[bool],
        typer.Option("--verbose", "-v", help="This flag enables verbose mode"),
    ] = False,
) -> None:
    """TaskCLI: A tool to help organize and list your tasks"""
    # basically this is the first thing that runs when app() is called
    # we first check storage to generate the files and stuff if they dont exist, then
    # we create a context.obj to store the variables in
    # we also create a logger object thingy to actually log things

    # Args:
    #     context (typer.Context): Context object used by typer. You must use context.obj to store persistent values.
    #

    logger.remove()
    logger.add(
        storage.MAIN_FILEPATH / "app.log",
        rotation="12:00",
        level="DEBUG",
        format="{time:DD-MM-YYYY_HH:mm:ss} > {name}:{line} > {level}: {message} | {extra}",
    )

    storage.check_storage()
    task_manager: tasks.TasklistManager = tasks.TasklistManager()
    context_config: config.Config = config.Config()
    final_verbose_mode: bool = context_config.behaviour_settings.verbose_mode or verbose

    logger.debug(f"Verbose mode is {final_verbose_mode}")
    if final_verbose_mode:
        logger.add(
            sys.stderr,
            format="{time:DD-MM-YYYY_HH:mm:ss} > {name}:{line} > {level}: {message} | {extra}",
            level="DEBUG",
        )

    context.obj = ContextObject(task_manager, context_config, final_verbose_mode)
    logger.info(
        "App initialization done. Put all the variables needed in context.obj",
    )


def main():
    app()


if __name__ == "__main__":
    main()

# add duedates and make verbose mode work and also list filtering when listing tasks (release taskcli revamp after)
# make it so that you can change between tasklists (branches pretty much)
# add tags and task groups
# undo redo
