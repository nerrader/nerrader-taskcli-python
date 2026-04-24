from datetime import datetime as dt
from typing import Any

from dateparser import parse as dateparser
from loguru import logger

from taskcli import config
from taskcli import storage

# This file is for everything related to tasks.


class Task:
    """The task class, created when adding a task (for now it just immediately converts it to a dict though)"""

    VALID_PRIORITIES: tuple[str, str, str, str] = ("low", "medium", "high", "urgent")
    VALID_STATUSES: tuple[str, str, str, str] = ("on-hold", "todo", "doing", "done")

    # function rehydrate_loaded_tasks is the reason why we cant just remove the status from here
    def __init__(
        self, next_id: int, name: str, priority: str, status: str, duedate: dt | None
    ) -> None:
        self._id = next_id
        self.name = name
        self.status = status
        self.priority = priority
        self.duedate = duedate

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
        new_priority = new_priority.strip().lower().replace(" ", "")
        if new_priority not in self.VALID_PRIORITIES:
            raise ValueError(
                f"'{new_priority}' is not a valid priority. Must be one of {self.VALID_PRIORITIES}"
            )
        self._priority = new_priority

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, new_status):
        new_status = new_status.strip().lower().replace(" ", "")
        if new_status not in self.VALID_STATUSES:
            raise ValueError(
                f"'{new_status}' is not a valid status. Must be one of {self.VALID_STATUSES}"
            )
        self._status = new_status


class TasklistManager:
    """This class should validate the tasks parameters before putting them in the tasks class, and also
    do some other stuff to manipulate the tasklist correctly"""

    PLACEHOLDER_TASKS: dict[str, Any] = {"next_id": 1, "tasklist": []}

    def __init__(self) -> None:
        data = storage.load_json(storage.TASKS_FILEPATH)

        self.old_tasklist: list[dict[str, Any]] = data["tasklist"]

        # rehydrating the python dictionaries into classes
        self.tasklist = self._rehydrate_loaded_tasks()
        self._next_id: int = data["next_id"]

    @property
    def next_id(self):
        return self._next_id

    def increment_id(self):
        self._next_id += 1
        logger.debug("Incremented next ID by 1", current_next_id=self.next_id)

    def reset_next_id(self) -> None:
        """Should only be done in clear_tasklist()"""
        self._next_id = 1
        logger.info("Resetted next ID back to 1")

    def find_target_task(self, target_id: int) -> Task:
        """Finds the target task according to the target id passed as an argument,
        then sends the entire dictionary of the task with that ID

        Raises:
            ValueError: If target task was not found."""
        target_task = next(
            (task for task in self.tasklist if task.id == target_id), None
        )
        if not target_task:
            logger.debug(f"No target task found for {target_id}")
            raise ValueError(f"Could not find task with ID {target_id}")
        logger.debug("Found target task", task=target_task.to_dict())
        return target_task

    def parse_duedate(self, original_duedate: str) -> dt:
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

    def add_task(
        self,
        name: str,
        configs: config.Config,
        priority: str | None = None,
        status: str | None = None,
        duedate: dt | None = None,
    ) -> Task:
        """Adds a task to the tasklist, where the name and the priority provided will be the
        attribute values for the task.
        """
        # if no priority, set priority to default
        if not priority:
            logger.info("No priority found in add task function.", data=priority)
            priority = configs.default_priority
            logger.debug("Successfully set priority to default priority", data=priority)
        if not status:
            logger.info("No status found in add task function.")
            status = "todo"
            logger.debug("Successfully set status to 'todo' (default)", data=status)

        # duedate already parsed
        new_task: Task = Task(
            self.next_id,
            name,
            priority=priority,
            status=status,
            duedate=duedate,
        )
        self.tasklist.append(new_task)

        self.increment_id()
        self.save_tasks()

        return new_task

    def delete_task(self, task_id: int) -> None:
        """Finds the task with the task_id in passed in using find_target_task(), then removes
        it from the self.tasklist

        Args:
            task_id (int): The target ID
        """
        target_task = self.find_target_task(task_id)
        self.tasklist.remove(target_task)
        self.save_tasks()

    def _validate_update_contents(
        self,
        update_contents: dict[str, Any],
    ) -> dict[str, Any]:
        """
        MAY THIS ONLY BE USED ON FUNCTION update_task()

        It validates the update contents, returns the ones where values are not none,
        and returns a failed ResultManager if something is wrong.

        Args:
            update_contents (dict[str, Any]): The updated contents to validate

        Returns:
            dict[str, str | dt]: The validated updated contents

        Raises:
            ValueError: If the new validated update contents were empty.
        """

        validated_update_contents = {
            key: value for key, value in update_contents.items() if value
        }
        # do this later
        if not validated_update_contents:
            raise ValueError("There were no contents to update in the first place.")
        # the checking if its a valid_priority will be done in the class itself using @property.setter
        logger.debug(
            "The validated update contents", contents=validated_update_contents
        )
        return validated_update_contents

    def update_task(self, task_id: int, updated_contents: dict[str, Any]) -> None:
        """Updates tasks given the task_id and the updated_contents, updated_contents will be
        put through the helper function _validate_update_contents(), to help validate and get rid of
        unneccessary things in the updated_contents.

        Args:
            task_id (int): The task ID that is updated.
            updated_contents (dict[str, Any]): The contents of the tasks that will be updated using
            self.tasklist.update(updated_contents)
        """
        # checks if the task_id exists
        target_task = self.find_target_task(task_id)

        # the data for the new validated update contents
        updated_contents = self._validate_update_contents(updated_contents)

        # now to finally update it
        for key, value in updated_contents.items():
            setattr(target_task, key, value)

        self.save_tasks()

    def mark_task(self, task_id: int, updated_status: str) -> None:
        """Marks the targetted task with the new updated_status

        Args:
            task_id (int): The targetted task
            updated_status (str): The new updated status
        """
        target_task = self.find_target_task(task_id)

        target_task.status = updated_status
        self.save_tasks()

    def clear_tasklist(self) -> None:
        self.tasklist = []
        self.reset_next_id()
        self.save_tasks()

    def clear_done_tasks(self) -> None:
        """clears all the done tasks, and saves them."""
        self.tasklist = [task for task in self.tasklist if task.status != "done"]
        self.save_tasks()

    # make it a docstring later, so basically it rehydrates those dictionaries into classes
    def _rehydrate_loaded_tasks(self) -> list[Task]:
        """
        NOTE: THIS SHOULD ONLY BE USED IN THE __init__ FUNCTION OF TASK MANAGER CLASS

        Rehydrates and turns the loaded tasks from the tasklist.json into Task classes, as you cannot
        save python classes into a .json file. Therefore, when you load the file, what comes out is a python
        dictionary
        """
        # this will replace the dictionaries with task class objects
        rehydrated_tasklist: list[Task] = []
        for task in self.old_tasklist:
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
                )
            )
        logger.success("Rehydrated the tasklist with new task classes")
        logger.debug(
            "Rehydrated tasklist",
            rehydrated_tasklist=[task.to_dict() for task in rehydrated_tasklist],
        )
        return rehydrated_tasklist

    def save_tasks(self) -> None:
        """Turns all the tasks into a dictionary, then saves all the tasks in storage.TASKS_FILEPATH
        (json file for storing tasks filepath)"""

        # make the class objects dictionaries first
        saved_tasklist = [task.to_dict() for task in self.tasklist]
        storage.write_json(
            storage.TASKS_FILEPATH,
            {"next_id": self.next_id, "tasklist": saved_tasklist},
        )
        logger.success(f"Successfully saved tasks to {storage.TASKS_FILEPATH}")
