# CHANGELOG

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

- Nothing added yet!

## [3.0.2] - 2026-25-05

- Improved README.md layout and formatting
- Added config UI for the tasklists folder.
- Tweaked the output statements in the `tasklists` command.
- Fixed bug for first-time users where the histories folder couldn't be made.
- Fixed the version number, making the `--version` command up to date.

## [3.0.1] - 2026-05-20

- Refactored most of config.py to make the configuration wizard outside the class.
- Added the new questionary style to more prompts for consistency.
- Fixed the bug where the `add tasklists` command wasn't working.

## [3.0.0] - 2026-05-12

- Refactored most of the codebase to get rid of the redundant `TasklistManager` and `ListManager` class in tasks.py to switch to more functional programming.
- Added a new constants.py file to remove unnecessary dependency injection.
- Added a config `tasklists_dir_filepath` to change the folder/directory where the tasklists are saved at.
- Added new commands: `undo` and `redo`, to undo/redo past actions.
- Added a new history.py file to complement that feature.
- Added a new task property: `tags`. Know that this property is hidden from the `list` command by default, so you have to change it in the settings menu.
- Added a list filtering feature, you can now pass in extra command options in the `list` command to filter what tasks are visible.
- Added the ability to set duedate and tags attributes to None.
- Removed pip-audit from the dev-dependency lists.
- Removed the `reset` command due to redundancy, most of the times it would crash before reaching that commmand anyway.
- Improved documentation on some files by updating their information.
- Enhanced the README.md with better quick usage commmands and more information clarity for new users.
- Fixed some dependency vulnerabilities found by dependabot by updating some specific packages to the latest version.

## [2.1.0] - 2026-05-05

- Added compatibility for other OSes such as Linux and macOS.
- Added platformdirs module to help with developing the multi OS compatibility feature.
- Added a `--version` `-V` flag that shows the version of TaskCLI you're using.
- Added an icon to the main .exe in the .zip file, which you can see in `assets/`
- Added the vermin package to check the minimum python version, and changed `pyproject.toml` to match that.
- Added an `__init__.py` to make it a regular package.
- Deleted TaskCLI.spec from the repository.

## [2.0.0] - 2026-04-28

This version marks the release of the new feature: tasklists!

- Added the tasklists feature, which allows you to add, delete, rename, and switch between tasklists, with the use of one subcommand: `tasklist`.
- Added a real README.md to my project.
- Removed the visibility of aliases of commands in help menu. It's now in the individual commands help menu context.
- Modified the pyproject.toml to move types-dateparser to dev-dependencies, and to remove rich from the main dependency section.

## [1.0.0] - 2026-04-24

This version marks the initial release of the TaskCLI.

- Added core features like adding, removing, updating, marking, listing tasks.
- Added other task attributes such as priority and duedate.
- Added customizable settings you can configure yourself using the `config` command.
- Added logging using loguru, saved in `AppData\Roaming\taskcli` in `app.log`.
- Added more destructive commands, like `clear` to clear your entire tasklist, or `reset` for a full factory reset of your taskcli and configs.

[Unreleased]: https://github.com/nerrader/nerraders-taskcli/compare/v3.0.1...HEAD
[3.0.2]: https://github.com/nerrader/nerraders-taskcli/compare/v3.0.1...v3.0.2
[3.0.1]: https://github.com/nerrader/nerraders-taskcli/compare/v3.0.0...v3.0.1
[3.0.0]: https://github.com/nerrader/nerraders-taskcli/compare/v2.1.0...v3.0.0
[2.1.0]: https://github.com/nerrader/nerraders-taskcli/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/nerrader/nerraders-taskcli/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/nerrader/nerraders-taskcli/releases/tag/v1.0.0
