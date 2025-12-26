# wfctl

Wayfire command line tool

## Installation

```bash
git clone https://github.com/killown/wfctl
cd wfctl
pip install .

Or, for editable/development mode:
pip install -e .
```

## Commands

| Command               | Description                                                                          |
| :-------------------- | :----------------------------------------------------------------------------------- |
| list views            | List all views currently available.                                                  |
| list outputs          | List all outputs connected to the system.                                            |
| search views          | Search for views by value and optionally by key: `wfctl search views {value} [key]`. |
| set workspace         | Switch to a specific workspace using its index.                                      |
| get focused output    | Get the currently focused output.                                                    |
| get focused view      | Get the currently focused view.                                                      |
| get focused workspace | Get the currently focused workspace index.                                           |
| next workspace        | Switch to the next available workspace.                                              |
| fullscreen view       | Set the fullscreen state of a view: `wfctl fullscreen view {view_id} {true/false}`.  |
| get view              | Get information about a specific view using a given {view_id}.                       |
| resize view           | Resize a specific view: `wfctl resize view {view_id} width height`.                  |
| move view             | Move a specific view: `wfctl move view {view_id} x-coordinate y-coordinate`.         |
| close view            | Close a view using a given {view_id}.                                                |
| minimize view         | Minimize a view: `wfctl minimize view {view_id} {true/false}`.                       |
| maximize view         | Maximize a view from a given {view_id}.                                              |
| set view alpha        | Set view transparency: `wfctl set view alpha {view_id} {0.4}`.                       |
| -m                    | Watch Wayfire IPC events.                                                            |
| list inputs           | Lists all input devices currently available in the Wayfire environment.              |
| configure device      | Configure a device input: `wfctl configure device {device_id} {enable/disable}`.     |
| get option            | Get Wayfire config value: `wfctl get option section/option`.                         |
| set option            | Set Wayfire config value: `wfctl set option section/option=value`.                   |
| get keyboard          | Retrieve the current keyboard layout, variant, model and options.                    |
| set keyboard          | Set the keyboard layout, variant, model and options.                                 |
| enable plugin         | Enable a plugin by its name.                                                         |
| disable plugin        | Disable a plugin by its name.                                                        |
| status plugin         | Check the status (enabled/disabled) of a specific plugin.                            |
| install plugin        | Install a plugin from Git: `wfctl install plugin {repo_url} [plugin_name]`.          |
| update plugins        | Batch update all plugins installed via `wfctl` by rebuilding from their sources.     |
