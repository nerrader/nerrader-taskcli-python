import json
from pathlib import Path
from typing import Any
from loguru import logger
from taskcli import constants as const


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


def check_config_file() -> None:
    logger.debug("Checking storage for the config file")
    config_filepath = const.CONFIG_FILEPATH

    if not config_filepath.exists():
        config_filepath.parent.mkdir(parents=True, exist_ok=True)
        write_json(config_filepath, const.DEFAULT_CONFIG)

        logger.debug("Config file wasn't found, set configs to default")


def check_history_file(history_filepath: Path) -> None:
    logger.debug("Checking storage for the history file.")

    history_filepath.parent.mkdir(parents=True, exist_ok=True)
    if not history_filepath.is_file():
        write_json(history_filepath, const.PLACEHOLDER_HISTORY)


def check_tasklists(
    tasks_dir_filepath: Path,
) -> None:
    """checks if the files exist, if not it creates them and fills them with default data

    i think args are pretty self explanatory"""
    logger.debug("Checking storage")
    # make the tasks directory in the appdata if it doesn't exist
    tasks_dir_filepath.mkdir(parents=True, exist_ok=True)

    # check if the files exist, if not create them and fill them with default data
    tasklists = list(tasks_dir_filepath.glob("*.json"))
    if not tasklists:  # if empty
        # then create a main default tasklists with the placeholder tasks
        write_json(tasks_dir_filepath / "main.json", const.PLACEHOLDER_TASKS)
