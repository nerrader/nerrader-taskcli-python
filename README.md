# Nerrader's TaskCLI
This version of a TaskCLI is a tool that was born out of necessity. I always had my own problems organizing and trying to remember my tasks and responsibilities, which led to an unorganized life, frequently forgetting deadlines and oftentimes doing things at the last minute which has caused me so much stress over the years.

So I made this tool to get rid of my mental clutter and organize my tasks more. So I can focus my time and energy on actually doing my tasks.
# Features

- ### Core Features of a Task Manager
    Adding, deleting, updating, marking, listing tasks are all here.

- ### Customizable Settings
    This tool uses the `questionary` module to open up an interactive menu to customize the settings by typing out a command.

- ### Local Storage
    This tool does not require an internet connection to run. Meaning you can still manage and use all the features while being offline.
  
- ### Logging
    This tool uses the `loguru` module for logging and troubleshooting.
  
- ### Additional Commands
    This tool has some additional commands like `clear` to clear your entire tasklist, and `reset` to factory reset both your tasklist and configs, however the `reset` command is usually for if a critical bug happens and there is no other way to get the program to work.

- ### Additional Task Attributes
    This tool has additional task attributes like priority, and duedates.

# How to Download/Install

> [!NOTE]
> Before using this tool, make sure you have: Windows 10 or more, as it doesn't work on other OSes.

1. Download the latest .exe file from the latest [Release](https://github.com/nerrader/nerraders-mc-mod-downloader/releases)
2. Run the .exe file
3. If Windows flags the .exe as unrecognized, click on **More Info > Run Anyway**

    > _This happens because this tool is new and does not have a paid Certificate._
    
4. You're done!

# How to Use

You can give the program the command line arguments by going to the directory you downloaded the .exe on, and ...
You can figure out most of the commands and how the overall usage works by just using --help.

> [!NOTE]
> This tool creates a directory in AppData/Roaming/taskcli to store, and sometimes modfiy needed .json files for it to function.

Here are the list of the main commands in the CLI, and their general purpose.
Again, to find more about it's arguments and options and aliases, use --help to generate the help menu for that specific command.

#### Main TaskCLI Commands:
| Command | Required Arguments | Description |
| :--------: | :------------: | :---: |
| add | task_name | Adds a new task with that task name |
| delete | task_id | Removes a specific task from your list based on its unique ID. |
| update | task_id, updated_contents (name, priority, etc) | Updates that specific task with that unique task_id with the updated_contents |
| mark | task_id, updated_status | Marks that specific task with that unique task_id with the new updated_status |
| list | NONE | Lists all tasks in a table |
| config | NONE | Opens up the main configuration menu |
| clear | NONE | Asks the user for confirmation, then clears the tasklist |
| reset | NONE | Asks the user for confirmation, then resets the tasklist and configs to factory defaults |

> [!TIP] 
> Make sure to check and configure your settings to your liking before starting the download process, as defaults might be undesirable.
>
> #### Default Settings:
> | Setting/Config | Default Value | Description |
> | :--------: | :------------: | :---: |
> | Visible Columns | [ID, Name, Status, Priority, Duedate] | Columns displayed in the task table |
> | Default Priority | medium | The priority assigned to new tasks if the -p option is omitted. |
> | Auto Clear Done Tasks | False | If enabled, tasks marked as done are automatically deleted. |
> | Require Clear Confirmation | True | If enabled, requires confirmation before the clearing of a tasklist |
> | Require Delete Confirmation | False | If enabled, requires confirmation before deletion of a task |
> | Show Table Lines | True | If enabled, requires confirmation before deletion of a task |
> | Show Status Colors | True | If enabled, it will show status colors during the listing of a task |
> | Show Priority Colors | True | If enabled, it will priority colors during the listing of a task |
> | Show Duedate Colors | True | If enabled, it will duedate colors during the listing of a task |
> | Verbose Mode | False | Enables detailed logging for troubleshooting |

# Upcoming/Planned Features

Here are some features that will be planned for future major/minor releases.

- Undo/Redo commands
- Adding, removing, and changing between different tasklists.
- Adding task tags or groups.
- Compatibility with other OS

# Contributing

This project welcomes all contributors, and whether you are fixing a bug, adding a new feature, or just improving the documentation of this project, you can get started by just following these steps:

1. Fork this repository
2. Clone this repository on your computer `https://github.com/[YOUR-USERNAME]/nerrader-taskcli-python.git`
3. It is recommended that you make a seperate branch than the main branch `git switch -c feature/new-feature`, using `feature/` for new features, and `fix/` to fix a known issue/bug, just to name a few.
4. Use `uv sync` to automatically set up the virtual environment and grab all the dependencies for you.
5. Commit your changes. Make sure your commit messages are clear and concise.
6. Push changes to your fork of the repository
7. Open a pull request. If you go back to the original repository, there should be a button called Compare & Pull Request. Click it, and one should be automaticallly made for you. Describe your changes and why they should be implemented in the main repository, then submit.

> [!IMPORTANT]
> Please make sure your code works properly before submitting. Follow PEP 8 guidelines, maintain consistent styling, and include type annotations and documentation for any new functions.

By contributing this project, you agree that your contribution will be licensed under the MIT License.

# Project Module Technical Stack
This project does use some python modules and packages to help with the development process. So I thought it would be helpful If I documented them here:

### Main Project Dependencies
- Typer: To handle the main CLI arguments and the --help menu.
- Rich: To handle the color styling, and listing tables, just to make it more aesthetically pleasing to look at.
- Questionary: For the confirmation prompts and the main settings configuration UI.
- Dateparser: To help with parsing and validating the duedates that the user passes in.
- Loguru: To enable logging in the app.log and verbose mode.

### Developer Dependencies
- Mypy: For type checking and error catching.
- Pip-aduit: For checking security vulnerabilities in packages.
- Pyinstaller: To make the distributable .exe file you are seeing in the releases.
- Radon: To help with measuring CC and MI in my code.
- Ruff: For code linting and formatting.
- Types-dateparser: To enable mypy to scan dateparser types.
- Vulture: For catching dead code

