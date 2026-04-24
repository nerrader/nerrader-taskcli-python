from glob import glob  # for resetting the .json files
import json
import os
from pathlib import Path
from typing import Any

from loguru import logger

MAIN_FILEPATH: Path = (
    Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "taskcli"
)
CONFIG_FILEPATH: Path = MAIN_FILEPATH / "config.json"
TASKS_FILEPATH: Path = MAIN_FILEPATH / "tasks.json"

# This file is for anything related to reading and writing to files in the main filepath


def load_json(filepath: Path) -> Any:
    try:
        logger.debug(f"Attemping to read JSON from {filepath}")
        with open(filepath, "r", encoding="utf-8") as file:
            file_contents = json.load(file)
    except FileNotFoundError:
        file_contents = None
        logger.error("File was not found in the designated filepath, returning None")
    return file_contents


def write_json(filepath: Path, data: Any) -> None:
    logger.debug(f"Writing data to {filepath}", write_data=data)
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def check_storage(default_tasks: dict, default_config: dict) -> None:
    """checks if the files exist, if not it creates them and fills them with default data"""
    logger.debug("Checking storage")
    # make the main directory and logs directory in the appdata if it doesn't exist
    os.makedirs(MAIN_FILEPATH, exist_ok=True)

    # check if the files exist, if not create them and fill them with default data
    if not TASKS_FILEPATH.exists():
        logger.debug("Tasklist file wasn't found, set tasks to the starting tasklist.")
        write_json(TASKS_FILEPATH, default_tasks)
    if not CONFIG_FILEPATH.exists():
        logger.debug("Config file wasn't found, set configs to default")
        write_json(CONFIG_FILEPATH, default_config)


def reset_files() -> None:
    files_to_reset = glob(os.path.join(MAIN_FILEPATH, "*.json"))
    if len(files_to_reset) <= 0:
        print("There was nothing to reset.")
    for file in files_to_reset:
        os.remove(file)
        logger.debug(f"Deleted {file}")
    logger.success("Successfully resetted tasklist and settings")
