from taskcli import storage
from typing import Any
from dataclasses import dataclass


class Task:
    """The task class, created when adding a task (for now it just immediately converts it to a dict though)"""

    VALID_PRIORITIES: tuple[str, str, str, str] = ("low", "medium", "high", "urgent")
    VALID_STATUSES: tuple[str, str] = ("todo", "done")

    def __init__(self, next_id: int, name: str, priority: str) -> None:
        self._id = next_id
        self.name = name
        self.status = "todo"
        self.priority = priority

    def to_dict(self) -> dict[str, Any]:
        """Turns the Task class object into a dictionary

        This is becasue Task class objects cannot be saved into a json file, you have to
        turn it into a dictionary first.
        """
        return {
            "id": self._id,
            "name": self.name,
            "status": self.status,
            "priority": self.priority,
        }

    # TODO: i just fucking realized ts doesnt do shit cuz you turn the class into a dict immediately
    # TODO: make this into a class, dont turn it into a dict, make rehydration
    @property
    def id(self):
        return self._id

    # @property
    # def priority(self):
    #     return self._priority

    # @priority.setter
    # def priority(self, new_priority):
    #     new_priority = new_priority.strip().lower().replace(" ", "")
    #     if new_priority not in self._VALID_PRIORITIES:
    #         raise ValueError(
    #             f"CRITICAL. Developer Error: '{new_priority}' is not a valid priority."
    #         )
    #     self._priority = new_priority

    # @property
    # def status(self):
    #     return self._status

    # @status.setter
    # def status(self, new_status):
    #     new_status = new_status.strip().lower().replace(" ", "")
    #     if new_status not in self._VALID_STATUSES:
    #         raise ValueError(
    #             f"CRITICAL. Developer Error: '{new_status}' is not a valid status."
    #         )
    #     self._status = new_status


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
        storage.check_storage()
        data = storage.json_io(storage.TASKS_FILEPATH)
        self.tasklist: list[dict[str, Any]] = data["tasklist"]
        self._next_id: int = data["next_id"]

    def find_target_task(self, target_id: int) -> dict[str, Any] | None:
        """Finds the target task according to the target id passed as an argument,
        then sends the entire dictionary of the task with that ID"""
        return next((task for task in self.tasklist if task["id"] == target_id), None)

    def add_task(self, name: str, priority: str) -> ResultManager:
        """Adds a task to the tasklist, where the name and the priority provided will be the
        attribute values for the task.

        Returns:
            ResultManager: The message that will be printed in the terminal in main.py
        """
        new_task = Task(self._next_id, name, priority)
        self.tasklist.append(new_task.to_dict())
        self._next_id += 1
        self.save_tasks()
        return ResultManager(
            True,
            f"Successfully added task '{name}' with priority '{priority}' with ID {new_task.id}",
        )

    def delete_task(self, task_id: int) -> ResultManager:
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")
        self.tasklist.remove(target_task)
        self.save_tasks()
        return ResultManager(True, f"Successfully deleted task with ID {task_id}")

    def _validate_update_contents(
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
            if not (value.strip() if value is not None else None)
        }
        if not validated_update_contents:
            return ResultManager(False, "There were no contents to update")
        updated_priority = validated_update_contents.get(
            "priority", "no_updated_priority"
        )
        if (
            updated_priority not in Task.VALID_PRIORITIES
            and updated_priority != "no_updated_priority"
        ):
            return ResultManager(False, f"'{updated_priority}' is not a valid_priority")
        return ResultManager(
            True, "Updated contents seems good", validated_update_contents
        )

    def update_task(
        self, task_id: int, updated_contents: dict[str, Any]
    ) -> ResultManager:
        results = self._validate_update_contents(updated_contents)
        if not results[0]:
            return ResultManager(
                False, f"The updated contents were not valid: {results[1]}"
            )
        updated_contents = results[2]  # the data
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")
        target_task.update(updated_contents)
        self.save_tasks()
        return ResultManager(True, f"Successfully updated task ID {task_id}")

    def mark_task(self, task_id: int, updated_status: str) -> ResultManager:
        target_task = self.find_target_task(task_id)
        if not target_task:
            return ResultManager(False, f"Could not find task with ID {task_id}")
        target_task["status"] = updated_status
        self.save_tasks()
        return ResultManager(
            True, f"Successfully updated task ID {task_id} with status {updated_status}"
        )

    def clear_tasklist(self) -> ResultManager:
        self.tasklist = []
        self._next_id = 1
        self.save_tasks()
        return ResultManager(True, "Successfully cleared all tasks in tasklist!")

    def save_tasks(self) -> None:
        """saves all the tasks in storage.TASKS_FILEPATH (json file for storing tasks filepath)"""
        storage.json_io(
            storage.TASKS_FILEPATH,
            {"next_id": self._next_id, "tasklist": self.tasklist},
        )
