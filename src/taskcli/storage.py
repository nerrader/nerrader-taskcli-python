import json
from pathlib import Path
from os import makedirs, getenv
from typing import Any
from taskcli import config

# Just know that config is not implemented yet!
MAIN_FILEPATH: Path = (
    Path(getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "taskcli"
)
CONFIG_FILEPATH: Path = MAIN_FILEPATH / "config.json"
TASKS_FILEPATH: Path = MAIN_FILEPATH / "tasks.json"
DEFAULT_TASKS: dict[str, Any] = {"next_id": 1, "tasklist": []}


def json_io(filepath: Path, data: Any = None) -> Any:
    """handles reading and writing to files

    Args:
        filepath (Path): the filepath of the file
        data (Any, optional): the data to write to the file, if none is provided, the function will read from the file.
        Defaults to None.

    Returns:
        Any: the data read from the file or None if an error occurs or if it was writing
    """
    # reading mode
    if data is None:
        try:
            with open(filepath, "r") as file:
                file_contents = json.load(file)
        except FileNotFoundError:
            file_contents = None
        return file_contents
    # writing mode
    else:
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)


def check_storage() -> None:
    """checks if the files exist, if not it creates them and fills them with default data"""

    # make the main directory if it doesn't exist
    makedirs(MAIN_FILEPATH, exist_ok=True)

    # check if the files exist, if not create them and fill them with default data
    if not TASKS_FILEPATH.exists():
        json_io(TASKS_FILEPATH, DEFAULT_TASKS)
    if not CONFIG_FILEPATH.exists():
        json_io(CONFIG_FILEPATH, config.Config.DEFAULT_CONFIG)


def main():
    check_storage()


if __name__ == "__main__":
    main()
