from copy import deepcopy
from dataclasses import dataclass, asdict, fields
from pathlib import Path
import tkinter as tk
from tkinter import filedialog

import questionary
from loguru import logger

from taskcli import constants as const
from taskcli import storage

# This file is for everything related to configs
print = const.CONSOLE.print


@dataclass
class BehaviourConfig:
    auto_clear_done_tasks: bool
    require_clear_confirmation: bool
    require_delete_confirmation: bool
    show_table_lines: bool
    show_priority_colors: bool
    show_status_colors: bool
    show_duedate_colors: bool
    verbose_mode: bool

    def __setattr__(self, name, value):
        """This makes sure that every value in this class is a boolean, as any other data type is invalid."""

        if name not in [field.name for field in fields(BehaviourConfig)]:
            raise TypeError(f"'{name}' is not a valid property name")
        if not isinstance(value, bool):
            raise TypeError(
                f"Invalid value: '{value}'. Behaviour Settings can only be set to a boolean value (True/False)"
            )
        object.__setattr__(self, name, value)
        logger.debug(f"Set {name} to {value} in behaviour config")


class Config:
    VALID_VISIBLE_COLUMNS: tuple[str, str, str, str, str, str] = (
        "ID",
        "Name",
        "Status",
        "Priority",
        "Duedate",
        "Tags",
    )

    def __init__(self) -> None:
        data: dict = self.load_configs()

        self._visible_columns: list[str] = data["visible_columns"]
        self._default_priority: str = data["default_priority"]
        self.current_tasklist: str = data["current_tasklist"]
        self.tasklists_dir_filepath: Path = Path(data["tasklists_dir_filepath"])
        self._behaviour_settings: BehaviourConfig = BehaviourConfig(
            **data["behaviour_settings"]
        )

    @property
    def visible_columns(self) -> list[str]:
        return self._visible_columns

    @visible_columns.setter
    def visible_columns(self, new_visible_columns_list: list[str]):
        if (
            not isinstance(new_visible_columns_list, list)
            or len(new_visible_columns_list) <= 0
        ):
            logger.error(
                "Could not set the new visible columns list as it had nothing to begin with, or it wasn't a list"
            )
            raise TypeError("The new visible columns settings have nothing.")

        invalid_column = next(
            (
                column
                for column in new_visible_columns_list
                if column not in self.VALID_VISIBLE_COLUMNS
            ),
            None,
        )
        if invalid_column:
            logger.error(
                f"Could not set new visible columns list: {new_visible_columns_list}. There was an invalid item in the visible columns config list: '{invalid_column}'"
            )
            raise TypeError(
                f"There is an invalid item in the visible columns config list: '{invalid_column}'"
            )
        self._visible_columns = new_visible_columns_list
        logger.debug(
            "Changed visible columns list", new_visible_columns=new_visible_columns_list
        )

    @property
    def default_priority(self) -> str:
        return self._default_priority

    @default_priority.setter
    def default_priority(self, new_default: str) -> None:
        if (
            not isinstance(new_default, str)
            or new_default not in const.VALID_PRIORITIES
        ):
            logger.error(
                f"The new default priority was not set as it wasn't valid: {new_default}"
            )
            raise TypeError(
                f"The new default priority value is not valid: {new_default}"
            )
        self._default_priority = new_default

    @property
    def behaviour_settings(self) -> BehaviourConfig:
        return self._behaviour_settings

    @behaviour_settings.setter
    def behaviour_settings(self, new_behaviour_settings: BehaviourConfig) -> None:
        if not isinstance(new_behaviour_settings, BehaviourConfig):
            raise TypeError(
                "The new behaviour config is not of dataclass 'BehaviourConfig'."
            )
        self._behaviour_settings = new_behaviour_settings

    def load_configs(self) -> dict:
        config_json: dict = storage.load_json(const.CONFIG_FILEPATH)
        return config_json

    def save_config(self):
        data = {
            "visible_columns": self._visible_columns,
            "default_priority": self._default_priority,
            "current_tasklist": self.current_tasklist,
            "tasklists_dir_filepath": str(self.tasklists_dir_filepath),
            "behaviour_settings": asdict(self._behaviour_settings),
        }
        storage.write_json(const.CONFIG_FILEPATH, data)
        logger.success("Successfully saved configs")

    def reset_defaults(self) -> None:
        """
        NOTE: meant to be used in main_configuration_ui(), but maybe can be used somewhere else.
        name is self explanatory i think
        """
        defaults = const.DEFAULT_CONFIG
        self.visible_columns = defaults["visible_columns"]
        self.default_priority = defaults["default_priority"]
        self.current_tasklist = defaults["current_tasklist"]
        self.tasklists_dir_filepath = defaults["tasklists_dir_filepath"]
        self.behaviour_settings = BehaviourConfig(**defaults["behaviour_settings"])
        logger.info("User has reset the configuration settings back to default.")


def _configure_table_column_visibility(current_visible_columns: list[str]) -> list[str]:
    """
    NOTE: THIS FUNCTION SHOULD ONLY BE CALLED IN main_configuration_ui()

    asks the user for which columns should be visible during the list_tasks() using a questionary.checkbox
    prompt, then saves that result directly in self.visible_columnss
    """
    logger.debug("User navigated to the configure table column visibility menu")
    new_visible_columns = questionary.checkbox(
        "What columns do you want enabled when tasks are being listed?",
        choices=[
            questionary.Choice(
                title=column_name, checked=column_name in current_visible_columns
            )
            for column_name in Config.VALID_VISIBLE_COLUMNS
        ],
        style=const.QUESTIONARY_STYLE,
    ).ask()

    # to check if the user did a ctrl + c, and to stop it being overriden if so
    if new_visible_columns:
        logger.info(f"Changed visible columns: {new_visible_columns}")
        return new_visible_columns
    else:
        logger.info("User cancelled visible columns change")
        return current_visible_columns


def _configure_default_priority(current_default_priority: str) -> str:
    """NOTE: THIS SHOULD ONLY BE USED ON main_configuration_ui()

    Configures the default priority using a questionary.select() prompt
    """
    logger.debug("User navigated to the configure default priority menu")
    new_default_priority = questionary.select(
        "What should be your new default priority when creating tasks?",
        choices=("low", "medium", "high", "urgent"),
        default=current_default_priority,
        style=const.QUESTIONARY_STYLE,
    ).ask()

    # checks for ctrl + c, because it returns none if it got cancelled
    if new_default_priority:
        logger.info(f"User changed default priority to {new_default_priority}")
        return new_default_priority
    else:
        logger.info("User cancelled default priority changes")
        return current_default_priority


def _configure_tasklist_filepath(current_tasklist_dir_filepath: Path) -> Path:
    """NOTE: THIS SHOULD ONLY BE USED ON main_configuration_ui()

    Configures the tasklist filepath directory used to store your tasklists, using questionary.path()
    to ask the user where to store it.
    """
    logger.debug("User navigated to the configure tasklist filepath menu")

    root = tk.Tk()
    root.withdraw()  # Hide the main window

    try:
        root.wm_attributes("-topmost", True)
    except tk.TclError:
        pass

    selected_folder_path = filedialog.askdirectory(
        title="Select new Tasklist Directory",
        initialdir=current_tasklist_dir_filepath,
        mustexist=True,
    )

    root.destroy()

    # checks for ctrl + c, because it returns none if it got cancelled
    if selected_folder_path:
        logger.info(f"User changed the tasklist folderpath to {selected_folder_path}")
        return Path(selected_folder_path)
    else:
        logger.info("User cancelled tasklist folderpath changes")
        return current_tasklist_dir_filepath


def _configure_behaviour_settings(
    current_behaviour_settings: BehaviourConfig,
) -> BehaviourConfig:
    """NOTE: THIS SHOULD ONLY BE USED ON main_configuration_ui()

    Configures the behaviour settings using questionary.checkbox()
    """
    logger.debug("User navigated to the configure behaviour settings menu")
    new_behaviour_settings: BehaviourConfig = deepcopy(current_behaviour_settings)

    behaviour_setting_names: list[str] = [
        field.name for field in fields(new_behaviour_settings)
    ]

    behaviour_setting_selection = questionary.checkbox(
        "Behaviour Settings:",
        choices=[
            questionary.Choice(
                title=setting.replace("_", " ").title(),
                value=setting,
                checked=getattr(new_behaviour_settings, setting),
            )
            for setting in behaviour_setting_names
        ],
        style=const.QUESTIONARY_STYLE,
    ).ask()

    # check for ctrl c cancels
    if behaviour_setting_selection is None:
        return current_behaviour_settings

    for behaviour_setting in behaviour_setting_names:
        if behaviour_setting in behaviour_setting_selection:
            setattr(new_behaviour_settings, behaviour_setting, True)
            continue
        setattr(new_behaviour_settings, behaviour_setting, False)
    return new_behaviour_settings


def _save_and_exit(new_config: Config, original_config: Config) -> None:
    """This function checks if the tasklists dir filepath has changed, and asks the user

    Args:
        original_config (Config): The original config

    Raises:
        ValueError: If the new config taskslist filepath is not a directory, raise this error.
    """

    if original_config.tasklists_dir_filepath == new_config.tasklists_dir_filepath:
        new_config.save_config()
        return

    move_tasklists = questionary.confirm(
        "Do you want to move all your existing tasklists into the new folder?",
        style=const.QUESTIONARY_STYLE,
    ).ask()

    if move_tasklists:
        for filepath in original_config.tasklists_dir_filepath.iterdir():
            filepath.move_into(new_config.tasklists_dir_filepath)
        print("Successfully changed the tasklists folderpath!", style="success")
    new_config.save_config()


def main_configuration_ui(original_config: Config) -> None:
    """pretty self explanatory, it creates the main configuration ui"""
    logger.info("User entered main setting configuration UI")

    # im getting a new config specifically for _save_and_exit()
    new_config = deepcopy(original_config)
    while True:
        main_selection = questionary.select(
            "Which setting do you want to configure?",
            choices=(
                "Table Column Visibility",
                "Default Task Priority",
                "Change Tasklists Folder",
                "Other Behaviour Settings",
                questionary.Separator(),
                "Save and Exit",
                "Set Defaults",
                "Cancel All Changes",
            ),
            style=const.QUESTIONARY_STYLE,
        ).ask()

        match main_selection:
            case "Table Column Visibility":
                new_config.visible_columns = _configure_table_column_visibility(
                    new_config.visible_columns
                )
            case "Default Task Priority":
                new_config.default_priority = _configure_default_priority(
                    new_config.default_priority
                )
            case "Change Tasklists Folder":
                new_config.tasklists_dir_filepath = _configure_tasklist_filepath(
                    new_config.tasklists_dir_filepath
                )
            case "Other Behaviour Settings":
                new_config.behaviour_settings = _configure_behaviour_settings(
                    new_config.behaviour_settings
                )
            case "Save and Exit":
                _save_and_exit(new_config, original_config)
                return
            case "Set Defaults":
                new_config.reset_defaults()
            case "Cancel All Changes":
                logger.info("User cancelled all changes")
                return
