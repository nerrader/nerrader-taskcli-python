from datetime import datetime as dt
from pathlib import Path
from typing import Any, TYPE_CHECKING

from dateparser import parse as dateparser
from loguru import logger

from taskcli import constants as const
from taskcli import storage

if TYPE_CHECKING:
    from taskcli import config


class Task:
    """The task class, created when adding a task (for now it just immediately converts it to a dict though)"""

    # function rehydrate_loaded_tasks is the reason why we cant just remove the status from here
    def __init__(
        self,
        next_id: int,
        name: str,
        priority: str,
        status: str,
        duedate: dt | None,
        tags: list[str] | None,
    ) -> None:
        self._id = next_id
        self.name = name
        self.status = status
        self.priority = priority
        self.duedate = duedate
        self.tags = tags

    def to_dict(self) -> dict[str, Any]:
        """Turns the Task class object into a dictionary

        This is becasue Task class objects cannot be saved into a json file, you have to
        turn it into a dictionary first.
        """
        # problem with duedate is that its a datetime object, objects cant be saved in json
        # so we make it an isostring and rehydrate it back to datetime later
        return {
            "id": self._id,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
            "duedate": self.duedate.isoformat() if self.duedate else None,
            "tags": self.tags,
        }

    def get_formatted_duedate(self) -> tuple[str, str]:
        """Returns the general duedate info needed for the list tasks function
        NOTE: THIS FUNCTION WAS ONLY MEANT TO BE USED IN list_tasks() in main.py

        Returns:
            tuple[str, str]: The first string contains the formatted duedate,
            the second one contains the desired color of the string
        """
        if not self.duedate:
            return ("None", "white")

        formatted_duedate = self.duedate.strftime("%d %b %Y %H:%M")
        time_diff = (self.duedate - (dt.now().astimezone())).total_seconds()

        # if overdue
        if time_diff < 0:
            color = "bold red"
        # if in one day
        elif time_diff < 86400:
            color = "orange3"
        # if in 3 days
        elif time_diff < 259200:
            color = "yellow"
        else:
            color = "green"

        return formatted_duedate, color

    @property
    def id(self):
        return self._id

    @property
    def priority(self):
        return self._priority

    @priority.setter
    def priority(self, new_priority):
        if not isinstance(new_priority, str):
            raise ValueError(
                f"'{new_priority}' is not a valid priority. Must be one of {const.VALID_PRIORITIES}"
            )
        new_priority = new_priority.strip().lower().replace(" ", "")
        if new_priority not in const.VALID_PRIORITIES:
            raise ValueError(
                f"'{new_priority}' is not a valid priority. Must be one of {const.VALID_PRIORITIES}"
            )
        self._priority = new_priority

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        if not isinstance(new_status, str):
            raise ValueError(
                f"'{new_status}' is not a valid status. Must be one of {const.VALID_STATUSES}"
            )
        new_status = new_status.strip().lower().replace(" ", "")
        if new_status not in const.VALID_STATUSES:
            raise ValueError(
                f"'{new_status}' is not a valid status. Must be one of {const.VALID_STATUSES}"
            )
        self._status = new_status


def _find_target_task(target_id: int, tasklist: list[Task]) -> Task:
    """Finds the target task according to the target id passed as an argument,
    then sends the entire dictionary of the task with that ID

    Raises:
        ValueError: If target task was not found."""
    target_task = next((task for task in tasklist if task.id == target_id), None)
    if not target_task:
        logger.debug(f"No target task found for {target_id}")
        raise ValueError(f"Could not find task with ID {target_id}")
    logger.debug("Found target task", task=target_task.to_dict())
    return target_task


def _parse_duedate(original_duedate: str) -> dt:
    """Validates the duedate by running it through a dateparser function, and catching if it returns None.

    Args:
        original_duedate (str): The original string for the unparsed duedate

    Returns:
        (dt): The datetime object.

    Raises:
        ValueError: If a duedate could not be parsed and it returns None, raise this error.
    """
    dateparse_settings = {
        "DATE_ORDER": "MDY",
        "RETURN_AS_TIMEZONE_AWARE": True,
    }
    parsed_duedate: dt | None = dateparser(
        original_duedate, settings=dateparse_settings
    )
    if not parsed_duedate:
        logger.error(f"Invalid duedate found: {original_duedate}. Setting to None.")
        raise ValueError(
            f"Invalid duedate string found: {original_duedate}. Setting to None.",
        )
    return parsed_duedate


def _string_split_comma(text: str) -> list[str]:
    """Splits a string (with commas) into a list of stripped strings.
    If the resulted string from splitting it is falsy, it will not be in the list

    Raises:
        ValueError: If it is not a string, or the string is falsy
        ValueError: The new list is empty"""

    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"This is not a valid string: '{text}'")
    if not (newlist := [item.strip() for item in text.split(",") if item.strip()]):
        raise ValueError("The list of strings are empty now.")
    return newlist


def add_task(
    task_properties: dict[str, Any],
    tasklist: list[Task],
    next_id: int,
    configs: config.Config,
) -> tuple[int, list[Task], Task]:
    """Adds a task to the tasklist, where the name and the priority provided will be the
    attribute values for the task.

    Args:
        task_properties (dict[str, Any]): The new task properties, like name or status.
        everything else is just self explanatory

    Returns (inside the tuple):
        int: The next_id
        list[Task]: The new and updated tasklist
        Task: The new task that was created
    """
    # variable initialization
    name: list[str] = task_properties["name"]
    status: str | None = task_properties["status"]
    priority: str | None = task_properties["priority"]
    duedate: str | None = task_properties["duedate"]
    tags: str | None = task_properties["tags"]

    # checking and refining the variables
    joined_name: str = (" ".join(name)).strip()
    parsed_duedate: dt | None = None
    if duedate:
        parsed_duedate = _parse_duedate(duedate)

    # refining the variables with defaults if none
    if not priority:
        logger.debug("No priority found in add task function.", data=priority)
        priority = configs.default_priority
        logger.debug("Successfully set priority to default priority", data=priority)
    if not status:
        logger.debug("No status found in add task function.")
        status = "todo"
        logger.debug("Successfully set status to 'todo' (default)", data=status)
    list_tags: list[str] | None = None
    if tags:
        list_tags = _string_split_comma(tags)

    new_task: Task = Task(
        next_id,
        joined_name,
        priority=priority,
        status=status,
        duedate=parsed_duedate,
        tags=list_tags,
    )

    # made a new variable so it doesnt modify the original one
    updated_tasklist = tasklist + [new_task]
    next_id += 1
    return (next_id, updated_tasklist, new_task)


def delete_task(tasklist: list[Task], task_id: int) -> list[Task]:
    """Finds the task with the task_id in passed in using _find_target_task(), then removes
    it from the self.tasklist

    Args:
        task_id (int): The target ID
    """
    target_task = _find_target_task(task_id, tasklist)

    return [task for task in tasklist if task != target_task]


def _validate_update_contents(
    update_contents: dict[str, Any],
) -> dict[str, Any]:
    """
    NOTE: THIS SHOULD ONLY BE USED ON FUNCTION update_task()

    Validates and parses update contents, removing ones that are None

    Args:
        update_contents (dict[str, Any]): The updated contents to validate

    Returns:
        dict[str, Any]: The validated updated contents

    Raises:
        ValueError: If the new validated update contents were empty.
    """

    def is_reset(value) -> bool:
        if isinstance(value, str) and value.strip().lower() == "none":
            return True
        return False

    transforms = {
        "name": lambda name: (
            " ".join(name).strip() if isinstance(name, list) else name.strip()
        ),
        "priority": lambda priority: priority.strip(),
        "duedate": lambda duedate: (
            None if is_reset(duedate) else _parse_duedate(duedate)
        ),
        "tags": lambda tags: None if is_reset(tags) else _string_split_comma(tags),
    }

    validated_update_contents = {
        key: transformed
        for key, value in update_contents.items()
        if value and ((transformed := transforms[key](value)) or is_reset(value))
    }
    # do this later
    if not validated_update_contents:
        raise ValueError("There were no contents to update in the first place.")

    # the checking if its a valid_priority will be done in the class itself using @property.setter
    logger.debug("The validated update contents", contents=validated_update_contents)
    return validated_update_contents


def update_task(
    tasklist: list[Task], task_id: int, updated_contents: dict[str, Any]
) -> list[Task]:
    """Updates tasks given the task_id and the updated_contents, updated_contents will be
    put through the helper function _validate_update_contents(), to help validate and get rid of
    unneccessary things in the updated_contents.

    Args:
        i think the args are pretty self explanatory
        updated_contents (dict[str, Any]): The contents of the tasks that will be updated
    """
    target_task = _find_target_task(task_id, tasklist)

    updated_contents = _validate_update_contents(updated_contents)

    for key, value in updated_contents.items():
        setattr(target_task, key, value)

    # basically returns a new list with the task updated
    return [target_task if task.id == task_id else task for task in tasklist]


def mark_task(tasklist: list[Task], task_id: int, updated_status: str) -> list[Task]:
    """Marks the targetted task with the new updated_status.

    Returns:
        list[Task]: The new and updated tasklist
    """
    target_task = _find_target_task(task_id, tasklist)
    target_task.status = updated_status

    return [target_task if task.id == task_id else task for task in tasklist]


def clear_tasklist() -> tuple[list, int]:
    """Literally returns an empty list, and the next ID"""
    return ([], 1)


def clear_done_tasks(tasklist: list[Task]) -> list[Task]:
    """returns the tasklist but all the done tasks are cleared"""
    return [task for task in tasklist if task.status != "done"]


def load_tasks(tasklist_filepath: Path) -> tuple[list[dict[str, Any]], int]:
    """This just loads tasks from the retrospective tasklist json file.

    Args:
        tasklist_filepath (Path): The tasklist filepath to load the tasks in.

    Returns:
        tuple[list[dict[str, Any]], int]: _description_
    """
    data = storage.load_json(tasklist_filepath)
    tasklist = data["tasklist"]
    next_id = data["next_id"]
    return (tasklist, next_id)


def rehydrate_loaded_tasks(unhydrated_tasklist: list[dict[str, Any]]) -> list[Task]:
    """
    NOTE: THIS FUNCTION WAS MEANT TO BE USED IN initialize_tasks()

    Rehydrates and turns the loaded tasks from the tasklist.json into Task classes, as you cannot
    save python classes into a .json file. Therefore, when you load the file, what comes out is a python
    dictionary

    Returns the rehydrated list of task classes.
    """
    # this will replace the dictionaries with task class objects
    rehydrated_tasklist: list[Task] = []
    for task in unhydrated_tasklist:
        # Convert isostring back to datetime object
        raw_date = task.get("duedate")
        parsed_date = dt.fromisoformat(raw_date) if raw_date else None

        rehydrated_tasklist.append(
            Task(
                task["id"],
                task["name"],
                priority=task["priority"],
                status=task["status"],
                duedate=parsed_date,
                tags=task["tags"],
            )
        )
    logger.success("Rehydrated the tasklist with new task classes")
    return rehydrated_tasklist


def initialize_tasks(tasklist_filepath: Path) -> tuple[list[Task], int]:
    """Initializes the tasklist by combining the load_tasks and rehydrate_loaded_tasks() functions.

    Args:
        tasklist_filepath (Path): The tasklist filepath

    Returns (things in the tuple):
        list[Task]: The new initialized tasklist
        int: The next_id
    """
    logger.debug("Initializing tasks...")
    tasklist, next_id = load_tasks(tasklist_filepath)
    rehydrated_tasklist = rehydrate_loaded_tasks(tasklist)

    return (rehydrated_tasklist, next_id)


def save_tasks(tasklist_filepath, tasklist: list[Task], next_id: int) -> None:
    """Turns all the tasks into a dictionary, then saves all the tasks in the tasklist_filepath
    (json file for storing tasks filepath)"""

    # make the class objects dictionaries first
    saved_tasklist = [task.to_dict() for task in tasklist]
    storage.write_json(
        tasklist_filepath,
        {"next_id": next_id, "tasklist": saved_tasklist},
    )
    logger.success(f"Successfully saved tasks to {tasklist_filepath}")


def _get_tasklists(taskslist_dir: Path) -> list[str]:
    """Always returns a fresh list of available tasklist names from disk."""
    return [file.stem for file in taskslist_dir.glob("*.json")]


def _resolve_tasklist_path(tasklist_dir: Path, name: str) -> Path:
    """Returns the combined tasklist directory and name, ensuring a .json extension."""
    return (tasklist_dir / name).with_suffix(".json")


def add_tasklist(tasklist_name: str, tasklist_directory: Path) -> None:
    tasklist_path = _resolve_tasklist_path(tasklist_directory, tasklist_name)
    storage.write_json(tasklist_path, const.PLACEHOLDER_TASKS)


def delete_tasklist(tasklist_name: str, tasklist_directory: Path) -> None:
    tasklists = _get_tasklists(tasklist_directory)
    tasklist_filepath = _resolve_tasklist_path(tasklist_directory, tasklist_name)
    if tasklist_name not in tasklists:
        raise ValueError(
            f"Tasklist name is not valid as it is not a real tasklist: {tasklist_name}"
        )
    if len(tasklists) == 1:
        raise ValueError(
            f"Cannot remove the {tasklist_name} tasklist as it would remove all the tasklists."
        )
    tasklist_filepath.unlink()


def rename_tasklist(
    old_tasklist_name: str,
    new_tasklist_name: str,
    tasklist_directory: Path,
) -> None:
    if old_tasklist_name not in _get_tasklists(tasklist_directory):
        raise ValueError(
            f"Tasklist name is not valid as it is not a real tasklist: {old_tasklist_name}"
        )

    _resolve_tasklist_path(tasklist_directory, old_tasklist_name).rename(
        _resolve_tasklist_path(tasklist_directory, new_tasklist_name)
    )


def switch_tasklists(tasklist_name: list[str], tasklists_dir_filepath: Path) -> str:
    joined_tasklist_name: str = (" ".join(tasklist_name)).strip()
    if joined_tasklist_name not in _get_tasklists(tasklists_dir_filepath):
        raise ValueError(
            f"Invalid tasklist name, as it doesn't exist: {joined_tasklist_name}"
        )

    return joined_tasklist_name


def list_tasklists(tasklists_dir_filepath: Path, current_tasklist: str) -> str:
    tasklists_message: str = ""
    for tasklist in _get_tasklists(tasklists_dir_filepath):
        if tasklist == current_tasklist:
            tasklists_message += f"[blue]- {tasklist} {'(CURRENT)' if tasklist == current_tasklist else ''}[/]\n"
            continue
        tasklists_message += f"- {tasklist}\n"
    return tasklists_message.strip()
