from datetime import datetime as dt
from dataclasses import dataclass
import sys  # we import sys for stderr for loguru specifically
from typing import Annotated

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


@app.command("add")
def add_task(
    context: typer.Context,
    name: Annotated[list[str], typer.Argument(help="The name of the task")],
    priority: Annotated[
        str | None,
        typer.Option("--priority", "-p", help="The priority of the created task"),
    ] = None,  # let the add_task() get the default priority later
    status: Annotated[
        str | None,
        typer.Option("--status", "-s", help="The status of the task"),
    ] = None,  # the __init__ in task class will automatically add a default value
    duedate: Annotated[
        str | None,
        typer.Option(
            "--duedate",
            "-d",
            help="The duedate of the task. Enter a shortcut (tomorrow, next week), or a date (MM-DD-YYYY)",
        ),
    ] = None,
) -> None:
    """Adds a task to the tasklist based on its name, priority, status, and duedates are set to default if not given.

    args are pretty self explanatory wont add them here, except for one:
    context (typer.Context): The context required to read and write to the needed global variables
    config (config.Config): only required to make the thing fill in the default priority if priority is not given by user
    """
    logger.info(
        "User invoked add command",
    )

    # literally just for the autocomplete really
    state: ContextObject = context.obj

    # to override the old list[str] so mypys happy
    joined_name: str = (" ".join(name)).strip()
    parsed_duedate: dt | None = None
    if duedate:
        parsed_duedate = state.task_manager.parse_duedate(duedate)

    # the add_task function will deal with the missing values themselves
    logger.debug(
        "task manager add task command_params",
        command_params={
            "name": joined_name,
            "priority": priority,
            "status": status,
            "duedate": parsed_duedate,
        },
    )
    new_task = state.task_manager.add_task(
        joined_name,
        state.config,
        priority,
        status,
        parsed_duedate,
    )
    logger.success("Appended new task to the tasklist")
    logger.debug(f"The new task contents: {new_task.to_dict()}")
    print(
        f"Successfully added new task '{new_task.name}' with ID {new_task.id} to the tasklist.",
        style="success",
    )
    display_tasks_table(context)


@app.command("delete")
@app.command("remove", help="Alias for delete command")
@app.command("del", help="Alias for delete command")
@app.command("rm", help="Alias for delete command")
def delete_task(
    context: typer.Context,
    task_id: Annotated[
        int, typer.Argument(help="The task id of the task being deleted")
    ],
) -> None:
    """Deletes a task based on its ID.

    Args:
        context (typer.Context): The context required to read and write to the needed global variables
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
        print("Task deletion cancelled", style="info")
        logger.info("Task deletion was cancelled")
        return

    state.task_manager.delete_task(task_id)
    logger.success(f"Succesfully deleted task with ID {task_id}")
    print(f"Successfully deleted task with ID {task_id}", style="success")
    display_tasks_table(context)


@app.command("update")
def update_task(
    context: typer.Context,
    task_id: int,
    updated_name: Annotated[
        list[str] | None, typer.Option("--name", "-n", help="The updated name")
    ] = None,
    updated_priority: Annotated[
        str | None,
        typer.Option("--priority", "-p", help="The updated priority"),
    ] = None,
    updated_duedate: Annotated[
        str | None,
        typer.Option(
            "--duedate",
            "-d",
            help="The duedate of the task. Enter a shortcut (tomorrow, next week), or a date (MM-DD-YYYY)",
        ),
    ] = None,
) -> None:
    """Updates a specific task given task ID. You can update the priority and duedate of the task. Does not allow updating statuses, use the mark command instead.

    Args:
        context (typer.Context): The context required to read and write to the needed global variables
        Other args are pretty self explanatory.
    """
    logger.info(
        "User invoked 'update' command",
    )

    # literally just for the autocomplete really
    state: ContextObject = context.obj

    joined_updated_name: str | None = " ".join(updated_name) if updated_name else None
    stripped_updated_priority = updated_priority.strip() if updated_priority else None
    parsed_updated_duedate = None

    if updated_duedate:
        parsed_updated_duedate = state.task_manager.parse_duedate(updated_duedate)

    raw_updated_contents = {
        "name": joined_updated_name,
        "priority": stripped_updated_priority,
        "duedate": parsed_updated_duedate or None,
    }
    logger.debug(
        "update command params",
        command_params={
            "task_id": task_id,
            "updated_name": joined_updated_name,
            "updated_priority": stripped_updated_priority,
            "updated_duedate": parsed_updated_duedate,
        },
    )

    state.task_manager.update_task(task_id, raw_updated_contents)
    logger.success(f"Successfully updated task with ID {task_id}")
    print(f"Successfully updated task with ID {task_id}", style="success")
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
    """Updates a task's status based on task ID.

    Args:
        context (typer.Context): The context required to read and write to the needed global variables
        task_id (int): The task ID given by the user
        updated_status (str): The updated status given by the user
    """
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

    # dw, the task class setter will deal with invalid statuses
    state.task_manager.mark_task(task_id, updated_status)
    logger.success(
        f"Successfully updated task ID {task_id} with status {updated_status}"
    )
    print(
        f"Successfully updated task ID {task_id} with status {updated_status}",
        style="success",
    )
    display_tasks_table(context)


def _get_styled_attribute(
    attribute: str, task: tasks.Task, config: config.Config
) -> str:
    """It gets the rich styled string (with colors) associated with the attribute,
    required for display_tasks_table()

    NOTE: This is meant to be used only in display_tasks_table(), using it elsewhere might causes unwanted results.

    Args:
        attribute (str): The attribute you want to change.
        task (tasks.Task): The task in which the attribute will be changed
        config (config.Config): The configs to comply with the user's behaviour settings.

    Raises:
        ValueError: If it is not a valid task attribute, raise this error.

    Returns:
        str: The rich stylized and colored string associated with that attribute.
    """
    attribute = attribute.lower().strip()  # for more leniency

    match attribute:
        case "id":
            return str(task.id)
        case "name":
            return task.name
        case "status":
            styled_status = f"[white]{task.status}[/]"
            if config.behaviour_settings.show_status_colors:
                status_colors: dict[str, str] = {
                    "on-hold": "dim",
                    "todo": "white",
                    "doing": "bold blue",
                    "done": "green4",
                }
                styled_status = f"[{status_colors[task.status]}]{task.status}[/]"
            return styled_status
        case "priority":
            styled_priority = f"[white]{task.priority}[/]"
            if config.behaviour_settings.show_priority_colors:
                priority_colors: dict[str, str] = {
                    "low": "green",
                    "medium": "yellow",
                    "high": "red",
                    "urgent": "bold red3",
                }
                styled_priority = (
                    f"[{priority_colors[task.priority]}]{task.priority}[/]"
                )
            return styled_priority
        case "duedate":
            formatted_duedate, task_duedate_color = task.get_formatted_duedate()
            return f"[{task_duedate_color}]{formatted_duedate}[/]"
        case _:
            raise ValueError(f"Not a valid attribute: '{attribute}'")


def display_tasks_table(context: typer.Context) -> None:
    """This is an internal CLI Command to display the rich table based off the tasklist."""
    # literally just for the autocomplete really
    state: ContextObject = context.obj

    if len(state.task_manager.tasklist) <= 0:
        print("There is nothing in the tasklist...", style="info")
        return

    # making the tables with the correct columns
    tasks_table = Table(
        title="The Tasklist",
        show_lines=state.config.behaviour_settings.show_table_lines,
    )
    for column_name in state.config.visible_columns:
        tasks_table.add_column(column_name)

    # where else am i supposed to put it
    # this auto clears all done tasks
    if state.config.behaviour_settings.auto_clear_done_tasks:
        state.task_manager.clear_done_tasks()

    for task in state.task_manager.tasklist:
        task_contents = [
            _get_styled_attribute(column_name, task, state.config)
            for column_name in state.config.visible_columns
        ]
        tasks_table.add_row(*task_contents)

    print("\n", tasks_table, "\n")
    # newlines to make it look better


@app.command("list")
@app.command("view", help="Alias for list command")
@app.command("ls", help="Alias for list command")
def list_tasks(context: typer.Context) -> None:
    """To list the tasks from the tasklist"""
    logger.info("User invoked 'list' command")
    """The actual CLI Command to list the rich table tasklist"""
    display_tasks_table(context)


@app.command("clear")
def clear_tasks(
    context: typer.Context,
    confirm: Annotated[
        bool,
        typer.Option("--confirm", "-c", help="Skips the confirmation prompt"),
    ] = False,
) -> None:
    """Asks a confirmation prompt first, then if they confirm, clear the tasklist.

    Args:
        context (typer.Context): The context required to read and write to the needed global variables
        confirm (bool): Defaults to False, if value is false, then confirmation is still required, otherwise, skip the prompt
    """
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
        print("Tasklist clear cancelled", style="info")
        logger.info("Cancelled clearing of tasklist")
        return
    state.task_manager.clear_tasklist()
    logger.success("Successfully cleared all tasks in tasklist!")


@app.command("config")
def config_cli(context: typer.Context) -> None:
    """To configure the TaskCLI settings.

    Args:
        context (typer.Context): The needed context to access and change the global variables.
    """
    logger.info("User invoked 'config' command")

    state: ContextObject = context.obj
    state.config.main_configuration_ui()


@app.command("reset")
def reset_files():
    """Resets all the user data including the taskcli and configs, does not include logs."""
    logger.info("User invoked 'reset' command")
    reset_confirm = questionary.confirm(
        "Are you sure you want to reset all your tasks and configs? NOTE: This won't reset app logs."
    ).ask()

    if reset_confirm:
        storage.reset_files()
        print("Successfully reset files!", style="success")
        logger.success("Successfully reset app data files!")


@app.callback()
def initialize(
    context: typer.Context,
    verbose: Annotated[
        bool,
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
        rotation="00:00",
        retention=0,
        level="DEBUG",
        format="{time:DD-MM-YYYY_HH:mm:ss} > {name}:{line} > {level}: {message} | {extra}",
    )

    storage.check_storage(
        tasks.TasklistManager.PLACEHOLDER_TASKS, config.Config.DEFAULT_CONFIG
    )
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

    context.obj = ContextObject(task_manager, context_config)
    logger.debug(
        "App initialization done. Put all the variables needed in context.obj",
    )


def main():
    try:
        app()
    except ValueError as error:
        # These are usually the errors raised by your setters (invalid priority, etc.)
        print(f"[bold red]Input Error:[/] {error}")
        logger.error(error)
        sys.exit(1)
    except KeyboardInterrupt:
        # Handles Ctrl+C gracefully without a messy traceback
        logger.debug("User did keyboard interrupt, operation cancelled")
        print("\n[yellow]Operation cancelled by user.[/]")
        sys.exit(0)
    except Exception as error:
        logger.opt(exception=True).critical("The app crashed unexpectedly.")
        print(f"[bold red]CRITICAL ERROR:[/] {error}")
        print("[dim]Please check the app.log for a full traceback.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
