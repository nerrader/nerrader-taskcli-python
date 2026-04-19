from dataclasses import dataclass, asdict, fields
from typing import Any

import questionary
from loguru import logger

from taskcli import storage
from taskcli import tasks

# This file is for everything related to configs


@dataclass
class BehaviourConfig:
    auto_clear_done_tasks: bool
    require_clear_confirmation: bool
    require_delete_confirmation: bool
    show_table_lines: bool
    show_priority_colors: bool
    show_status_colors: bool
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
    # These are the valid values for the visible_columns setting, it is a list of these values most of the time.
    VALID_VISIBLE_COLUMNS: tuple[str, str, str, str, str] = (
        "ID",
        "Name",
        "Status",
        "Priority",
        "Duedate",
    )
    DEFAULT_CONFIG: dict[str, Any] = {
        "visible_columns": ["ID", "Name", "Status", "Priority"],
        "default_priority": "medium",
        "behaviour_settings": {
            "auto_clear_done_tasks": False,
            "require_clear_confirmation": True,
            "require_delete_confirmation": False,
            "show_table_lines": True,
            "show_status_colors": True,
            "show_priority_colors": True,
            "verbose_mode": False,
        },
    }

    def __init__(self) -> None:
        data: dict = self.load_configs()

        self._visible_columns: list[str] = data["visible_columns"]
        self._default_priority: str = data["default_priority"]
        self._behaviour_settings: BehaviourConfig = BehaviourConfig(
            **data["behaviour_settings"]
        )

    @property
    def visible_columns(self):
        return self._visible_columns

    @visible_columns.setter
    def visible_columns(self, new_visible_columns_list: list[str]):
        if (
            not isinstance(new_visible_columns_list, list)
            or len(new_visible_columns_list) <= 0
        ):
            raise TypeError("The new visible columns settings have nothing.")
        # if there is an item in the visible columns list that is not in the valid_visible_columns constant defined in the class
        invalid_column = next(
            (
                column
                for column in new_visible_columns_list
                if column not in self.VALID_VISIBLE_COLUMNS
            ),
            None,
        )
        if invalid_column:
            raise TypeError(
                f"There is an invalid item in the visible columns config list: '{invalid_column}'"
            )
        self._visible_columns = new_visible_columns_list
        logger.debug(
            "Changed visible columns list", new_visible_columns=new_visible_columns_list
        )

    @property
    def default_priority(self):
        return self._default_priority

    @default_priority.setter
    def default_priority(self, new_default: str):
        if (
            not isinstance(new_default, str)
            or new_default not in tasks.Task.VALID_PRIORITIES
        ):
            raise TypeError(
                f"The new default priority value is not valid: {new_default}"
            )
        self._default_priority = new_default

    @property
    def behaviour_settings(self):
        return self._behaviour_settings

    @logger.catch(level="CRITICAL")
    def load_configs(self) -> dict:
        config_json: dict = storage.json_io(storage.CONFIG_FILEPATH)
        return config_json

    # pretty self explanatory i think
    @logger.catch(level="CRITICAL")
    def save_config(self):
        data = {
            "visible_columns": self._visible_columns,
            "default_priority": self._default_priority,
            "behaviour_settings": asdict(self._behaviour_settings),
        }
        storage.json_io(storage.CONFIG_FILEPATH, data)
        logger.success("Successfully saved configs")

    @logger.catch(level="ERROR")
    def _configure_table_column_visibility(self) -> None:
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
                    title=column_name, checked=column_name in self.visible_columns
                )
                for column_name in self.VALID_VISIBLE_COLUMNS
            ],
        ).ask()
        # to check if the user did a ctrl + c, and to stop it being overriden if so
        if new_visible_columns:
            self.visible_columns = new_visible_columns
            logger.info(f"Changed visible columns: {new_visible_columns}")
        else:
            logger.info("User cancelled visible columns change")
        return

    @logger.catch(level="ERROR")
    def _configre_default_priority(self) -> None:
        """NOTE: THIS SHOULD ONLY BE USED ON main_configuration_ui()

        Configures the default priority using a questionary.select() prompt
        """
        logger.debug("User navigated to the configure default priority menu")
        new_default_priority = questionary.select(
            "What should be your new default priority when creating tasks?",
            choices=("low", "medium", "high", "urgent"),
        ).ask()

        # checks for ctrl + c, because it returns none if it got cancelled
        if new_default_priority:
            self.default_priority = new_default_priority
            logger.info(f"User changed default priority to {new_default_priority}")
        else:
            logger.info("User cancelled default priority changes")
        return

    @logger.catch(level="ERROR")
    def _configure_behaviour_settings(self) -> None:
        """NOTE: THIS SHOULD ONLY BE USED ON main_configuration_ui()

        Configures the behaviour settings using questionary.checkbox()
        """
        logger.debug("User navigated to the configure behaviour settings menu")
        behaviour_setting_names = [
            setting
            for setting in (field.name for field in fields(self.behaviour_settings))
        ]

        behaviour_setting_selection = questionary.checkbox(
            "Behaviour Settings:",
            choices=[
                questionary.Choice(
                    # turns all words capitalized, and replaces "_" with spaces
                    title=setting.replace("_", " ").title(),
                    value=setting,
                    checked=getattr(self.behaviour_settings, setting),
                )
                for setting in behaviour_setting_names
            ],
        ).ask()

        # check for ctrl c cancels
        if behaviour_setting_selection is None:
            return

        for behaviour_setting in behaviour_setting_names:
            if behaviour_setting in behaviour_setting_selection:
                setattr(self.behaviour_settings, behaviour_setting, True)
                continue
            setattr(self.behaviour_settings, behaviour_setting, False)

    @logger.catch(level="ERROR")
    def reset_defaults(self) -> None:
        """
        NOTE: meant to be used in main_configuration_ui(), but maybe can be used somewhere else.
        name is self explanatory i think
        """
        defaults = self.DEFAULT_CONFIG
        self.visible_columns: list[str] = defaults["visible_columns"]
        self.default_priority: str = defaults["default_priority"]
        self._behaviour_settings = BehaviourConfig(**defaults["behaviour_settings"])
        logger.info("User has reset the configuration settings back to default.")

    @logger.catch(level="ERROR")
    def main_configuration_ui(self) -> None:
        """pretty self explanatory, it creates the main configuration ui"""
        # why dont you make a new_config variable?
        # well because if i cancel, the config wouldnt save anyway, and unless i decided to
        # make this app persistent, it will never save between sessions unless you save it first
        logger.info("User entered main setting configuration UI")
        while True:
            main_selection = questionary.select(
                "Which setting do you want to configure?",
                choices=(
                    "Table Column Visibility",
                    "Default Task Priority",
                    "Other Behaviour Settings",
                    questionary.Separator(),
                    "Exit and Save",
                    "Set Defaults",
                    "Cancel All Changes",
                ),
            ).ask()

            match main_selection:
                case "Table Column Visibility":
                    self._configure_table_column_visibility()
                case "Default Task Priority":
                    self._configre_default_priority()
                case "Other Behaviour Settings":
                    self._configure_behaviour_settings()
                case "Exit and Save":
                    self.save_config()
                    return
                case "Set Defaults":
                    self.reset_defaults()
                case "Cancel All Changes":
                    logger.info("User cancelled all changes")
                    return
