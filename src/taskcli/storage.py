from glob import glob
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

from taskcli import config

MAIN_FILEPATH: Path = (
    Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "taskcli"
)
CONFIG_FILEPATH: Path = MAIN_FILEPATH / "config.json"
TASKS_FILEPATH: Path = MAIN_FILEPATH / "tasks.json"
DEFAULT_TASKS: dict[str, Any] = {"next_id": 1, "tasklist": []}

# This file is for anything related to reading and writing to files in the main filepath


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
            logger.debug(f"Attemping to read JSON from {filepath}")
            with open(filepath, "r") as file:
                file_contents = json.load(file)
        except FileNotFoundError:
            file_contents = None
            logger.error(
                "File was not found in the designated filepath, returning None"
            )
        return file_contents
    # writing mode
    else:
        logger.debug(f"Writing data to {filepath}", write_data=data)
        with open(filepath, "w") as file:
            json.dump(data, file, indent=4)


def check_storage() -> None:
    """checks if the files exist, if not it creates them and fills them with default data"""
    logger.debug("Checking storage")
    # make the main directory and logs directory in the appdata if it doesn't exist
    os.makedirs(MAIN_FILEPATH, exist_ok=True)

    # check if the files exist, if not create them and fill them with default data
    if not TASKS_FILEPATH.exists():
        logger.debug("Tasklist file wasn't found, set tasks to the starting tasklist.")
        json_io(TASKS_FILEPATH, DEFAULT_TASKS)
    if not CONFIG_FILEPATH.exists():
        logger.debug("Config file wasn't found, set configs to default")
        json_io(CONFIG_FILEPATH, config.Config.DEFAULT_CONFIG)


def reset_files() -> None:
    files_to_reset = glob(os.path.join(MAIN_FILEPATH, "*.json"))
    if len(files_to_reset) <= 0:
        print("There was nothing to reset.")
    for file in files_to_reset:
        os.remove(file)
        logger.debug(f"Deleted {file}")
    logger.success("Successfully resetted tasklist and settings")
