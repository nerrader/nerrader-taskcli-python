from taskcli import storage
from taskcli import config
from typing import Any, Optional
from dataclasses import dataclass


class Task:
    """The task class, created when adding a task (for now it just immediately converts it to a dict though)"""

    VALID_PRIORITIES: tuple[str, str, str, str] = ("low", "medium", "high", "urgent")
    VALID_STATUSES: tuple[str, str, str, str] = ("on-hold", "todo", "doing", "done")

    # function rehydrate_loaded_tasks is the reason why we cant just remove the status from here
    def __init__(
        self,
        next_id: int,
        name: str,
        priority: str,
        status: str,
    ) -> None:
        self._id = next_id
        self.name = name
        self._status = status
        self._priority = priority

    def to_dict(self) -> dict[str, Any]:
        """Turns the Task class object into a dictionary

        This is becasue Task class objects cannot be saved into a json file, you have to
        turn it into a dictionary first.
        """
        return {
            "id": self._id,
            "name": self.name,
            "status": self._status,
            "priority": self._priority,
        }

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


@dataclass(frozen=True)
class ResultManager:
    """A dataclass for the result messages in tasklist manager functions."""

    success: bool
    message: str
    data: Any = None

    # This function runs if you want to print the resultmanager on the terminal
    # Only used in main.py
    def __rich__(self) -> str:
        color = "green" if self.success else "red"
        return f"[{color}]{self.message}[/{color}]"


class TasklistManager:
    def __init__(self) -> None:
        data = storage.json_io(storage.TASKS_FILEPATH)

        self.old_tasklist: list[dict[str, Any]] = data["tasklist"]

        # rehydrating the python dictionaries into classes
        self.tasklist = self._rehydrate_loaded_tasks()
        self._next_id: int = data["next_id"]

    @property
    def next_id(self):
        return self._next_id

    def increment_id(self):
        self._next_id += 1

    def reset_next_id(self) -> None:
        """Should only be done in clear_tasklist()"""
        self._next_id = 1

    def find_target_task(self, target_id: int) -> Task | None:
        """Finds the target task according to the target id passed as an argument,
        then sends the entire dictionary of the task with that ID"""
        return next((task for task in self.tasklist if task.id == target_id), None)

    def add_task(
        self, name: str, priority: Optional[str] = None, status: Optional[str] = None
    ) -> ResultManager:
        """Adds a task to the tasklist, where the name and the priority provided will be the
        attribute values for the task.

        Returns:
            ResultManager: The message that will be printed in the terminal in main.py
        """
        try:
            # if no priority, set priority to default
            if not priority:
                configs = config.Config()
                priority = configs.default_priority
            if not status:
                status = "todo"
            new_task: Task = Task(self.next_id, name, priority=priority, status=status)
            self.tasklist.append(new_task)
            self.increment_id()
            self.save_tasks()
            return ResultManager(
                True,
                f"Successfully added task '{name}' with priority '{priority}' with ID {new_task.id}",
            )
        except ValueError as error:
            # this valueerror only occurs if its an invalid priority or something, raised in task class setters
            error_message = str(error)
            return ResultManager(False, error_message)

    def delete_task(self, task_id: int) -> ResultManager:
        """Finds the task with the task_id in passed in using find_target-task(), then removes
        it from the self.tasklist

        Args:
            task_id (int): The target ID

        Returns:
            ResultManager: The results of the function
        """
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")
        self.tasklist.remove(target_task)
        self.save_tasks()
        return ResultManager(True, f"Successfully deleted task with ID {task_id}")

    def _validate_update_contents(
        self,
        update_contents: dict[str, Any],
    ) -> ResultManager:
        """
        MAY THIS ONLY BE USED ON FUNCTION update_task()

        It validates the update contents, returns the ones where values are not none,
        and returns a failed ResultManager if something is wrong.

        Args:
            update_contents (dict[str, Any]): The updated contents to validate

        Returns:
            ResultManager: The results returned by this function, containing either a failed
            one or a successful one with data.
        """

        validated_update_contents = {
            key: value
            for key, value in update_contents.items()
            if (
                value.strip() if value is not None else None
            )  # if value.strip() exists if value exists
        }
        if not validated_update_contents:
            return ResultManager(False, "There were no contents to update")
        # the checking if its a valid_priority will be done in the class itself using @property.setter
        return ResultManager(
            True, "Updated contents seems good", validated_update_contents
        )

    def update_task(
        self, task_id: int, updated_contents: dict[str, Any]
    ) -> ResultManager:
        """Updates tasks given the task_id and the updated_contents, updated_contents will be
        put through the helper function _validate_update_contents(), to help validate and get rid of
        unneccessary things in the updated_contents.

        Args:
            task_id (int): The task ID that is updated.
            updated_contents (dict[str, Any]): The contents of the tasks that will be updated using
            self.tasklist.update(updated_contents)

        Returns:
            ResultManager: The results of the function, giving a success/failure bool and a message of cause along with it.
        """
        # checks if the task_id exists
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")

        # checks if the update contents are valid
        results = self._validate_update_contents(updated_contents)
        if not results.success:
            return ResultManager(
                False, f"The updated contents were not valid: {results.message}"
            )
        updated_contents = (
            results.data
        )  # the data for the new validated update contents

        # now to finally update it
        for key, value in updated_contents.items():
            try:
                setattr(target_task, key, value)
            except ValueError as error:
                error_message = str(error)
                return ResultManager(False, error_message)

        self.save_tasks()
        return ResultManager(True, f"Successfully updated task ID {task_id}")

    def mark_task(self, task_id: int, updated_status: str) -> ResultManager:
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")

        try:
            target_task.status = updated_status
            self.save_tasks()
            return ResultManager(
                True,
                f"Successfully updated task ID {task_id} with status {updated_status}",
            )
        except ValueError as error:
            error_message = str(error)
            return ResultManager(False, error_message)

    def clear_tasklist(self) -> ResultManager:
        self.tasklist = []
        self.reset_next_id()
        self.save_tasks()
        return ResultManager(True, "Successfully cleared all tasks in tasklist!")

    # make it a docstring later, so basically it rehydrates those dictionaries into classes
    def _rehydrate_loaded_tasks(self) -> list[Task]:
        """
        NOTE: THIS SHOULD ONLY BE USED IN THE __init__ FUNCTION OF TASK MANAGER CLASS

        Rehydrates and turns the loaded tasks from the tasklist.json into Task classes, as you cannot
        save python classes into a .json file. Therefore, when you load the file, what comes out is a python
        dictionary
        """
        # this will replace the dictionaries with task class objects
        rehydrated_tasklist = [
            Task(
                task["id"],
                task["name"],
                priority=task["priority"],
                status=task["status"],
            )
            for task in self.old_tasklist
        ]
        return rehydrated_tasklist

    def save_tasks(self) -> None:
        """Turns all the tasks into a dictionary, then saves all the tasks in storage.TASKS_FILEPATH
        (json file for storing tasks filepath)"""

        # make the class objects dictionaries first
        saved_tasklist = [task.to_dict() for task in self.tasklist]
        storage.json_io(
            storage.TASKS_FILEPATH,
            {"next_id": self.next_id, "tasklist": saved_tasklist},
        )
