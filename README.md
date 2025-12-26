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
| -m                    | Watch Wayfire IPC events.                                                            |
| close view            | Close a view using a given {view_id}.                                                |
| configure device      | Configure a device input: `wfctl configure device {device_id} {enable/disable}`.     |
| disable plugin        | Disable a plugin by its name.                                                        |
| enable plugin         | Enable a plugin by its name.                                                         |
| fullscreen view       | Set the fullscreen state of a view: `wfctl fullscreen view {view_id} {true/false}`.  |
| get focused output    | Get the currently focused output.                                                    |
| get focused view      | Get the currently focused view.                                                      |
| get focused workspace | Get the currently focused workspace index.                                           |
| get keyboard          | Retrieve the current keyboard layout, variant, model and options.                    |
| get option            | Get Wayfire config value: `wfctl get option section/option`.                         |
| get view              | Get information about a specific view using a given {view_id}.                       |
| install plugin        | Install a plugin from Git: `wfctl install plugin {repo_url} [plugin_name]`.          |
| list config           | List live configuration from wayfire.ini: `wfctl list config [filter]`.              |
| list inputs           | Lists all input devices currently available.                                         |
| list outputs          | List all outputs connected to the system.                                            |
| list views            | List all views currently available.                                                  |
| maximize view         | Maximize a view from a given {view_id}.                                              |
| minimize view         | Minimize a view: `wfctl minimize view {view_id} {true/false}`.                       |
| move view             | Move a specific view: `wfctl move view {view_id} x-coordinate y-coordinate`.         |
| next workspace        | Switch to the next available workspace.                                              |
| resize view           | Resize a specific view: `wfctl resize view {view_id} width height`.                  |
| search views          | Search for views by value and optionally by key: `wfctl search views {value} [key]`. |
| set keyboard          | Set the keyboard layout by index: `wfctl set keyboard {index}`.                      |
| set option            | Set Wayfire config value: `wfctl set option section/option=value`.                   |
| set view alpha        | Set view transparency: `wfctl set view alpha {view_id} {0.4}`.                       |
| set workspace         | Switch to a specific workspace using its index.                                      |
| status plugin         | Check the status (enabled/disabled) of a specific plugin.                            |
| update plugins        | Batch update all plugins installed via `wfctl` by rebuilding from source.            |
