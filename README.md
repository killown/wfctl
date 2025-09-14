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

| Command                 | Description                                                                                          |
|-------------------------|------------------------------------------------------------------------------------------------------|
| list views              | List all views currently available.                                                                 |
| list outputs            | List all outputs connected to the system.                                                           |
| set workspace           | Switch to a specific workspace.                                                                     |
| get focused output      | Get the currently focused output.                                                                   |
| get focused view        | Get the currently focused view.                                                                     |
| get focused workspace   | Get the currently focused workspace.                                                                |
| next workspace          | Switch to the next workspace.                                                                       |
| fullscreen view         | Set fullscreen the view from the given id.                                                          |
| get view                | Get information about a specific view using a given {view_id}.                                      |
| resize view             | Resize a specific view: wfctl resize view {view_id} width height.                                   |
| move view               | Move a specific view: wfctl move view {view_id} x-coordinate y-coordinate.                           |
| close view              | Close a view using a given {view_id}.                                                              |
| minimize view           | Minimize a view: wfctl minimize view {view_id} {true/false}.                                        |
| maximize                | Maximize a view from a given id.                                                                    |
| set view alpha          | Set view transparency: wfctl set view alpha {view_id} {0.4}.                                        |
| -m                      | Watch Wayfire IPC events.                                                                           |
| list inputs             | Lists all input devices currently available in the Wayfire environment.                             |
| configure device        | Configure a device input: wfctl configure device {device_id} {enable/disable}.                      |
| get option              | Get Wayfire config value: wfctl get option section/option.                                           |
| set option              | Set Wayfire config value: wfctl set options section_1/option_1:value_1 section_2/option_2:value_2. |
| get keyboard            | Retrieve the current keyboard layout, variant, model and options.                                    |
| set keyboard            | Set the keyboard layout, variant, model and options.                                                |
| enable plugin           | Enable a plugin from a given name.                                                                  |
| disable plugin          | Disable a plugin from a given name.                                                                 |
