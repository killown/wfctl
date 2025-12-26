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

| Command                    | Description                                          | Example Usage                                       |
| :------------------------- | :--------------------------------------------------- | :-------------------------------------------------- |
| **-m**                     | Watch Wayfire IPC events in real-time.               | `wfctl -m`                                          |
| **audit plugins**          | Check Plugins ABI compatibility.                     | `wfctl audit plugins`                               |
| **check abi**              | Check ABI compatibility for a specific binary.       | `wfctl check abi /path/to/plugin.so`                |
| **close view**             | Close a specific view by its ID.                     | `wfctl close view 15`                               |
| **configure device**       | Enable or disable a specific input device.           | `wfctl configure device 12 enable`                  |
| **create output**          | Create a virtual headless display.                   | `wfctl create output 1920 1080`                     |
| **disable plugin**         | Deactivate a Wayfire plugin.                         | `wfctl disable plugin wobbly`                       |
| **enable plugin**          | Activate a Wayfire plugin.                           | `wfctl enable plugin expo`                          |
| **fullscreen view**        | Toggle or set fullscreen state.                      | `wfctl fullscreen view 7 true`                      |
| **get focused output**     | Show details of the active output.                   | `wfctl get focused output`                          |
| **get focused view**       | Show details of the active window.                   | `wfctl get focused view`                            |
| **get focused workspace**  | Get current workspace index.                         | `wfctl get focused workspace`                       |
| **get keyboard**           | List layouts and active layout index.                | `wfctl get keyboard`                                |
| **get log path**           | Retrieve current stdout redirection path.            | `wfctl get log path`                                |
| **get option**             | Read a specific configuration value.                 | `wfctl get option core/plugins`                     |
| **get view**               | Get full JSON info for a specific view ID.           | `wfctl get view 12`                                 |
| **install plugin**         | Build and install a plugin from Git.                 | `wfctl install plugin https://github.com/user/repo` |
| **list config**            | Search/list live configuration options.              | `wfctl list config blur`                            |
| **list inputs**            | Show all connected input devices.                    | `wfctl list inputs`                                 |
| **list outputs**           | Show all active physical and virtual outputs.        | `wfctl list outputs`                                |
| **list plugins**           | Show all installed Wayfire plugins and their status. | `wfctl list plugins`                                |
| **list views**             | Show all open windows and their properties.          | `wfctl list views`                                  |
| **list wsets**             | List all workspace sets (output groups).             | `wfctl list wsets`                                  |
| **maximize view**          | Maximize a specific window.                          | `wfctl maximize view 22`                            |
| **minimize view**          | Minimize or restore a window.                        | `wfctl minimize view 22 true`                       |
| **move view**              | Move window to specific coordinates.                 | `wfctl move view 15 100 150`                        |
| **move view to workspace** | Send window to a different workspace grid.           | `wfctl move view to workspace 15 1 1`               |
| **next workspace**         | Cycle to the next workspace.                         | `wfctl next workspace`                              |
| **register binding**       | Create a dynamic global hotkey.                      | `wfctl register binding "<alt>KEY_T" "kitty"`       |
| **resize view**            | Change window dimensions.                            | `wfctl resize view 12 800 600`                      |
| **search views**           | Filter views by property or value.                   | `wfctl search views firefox app-id`                 |
| **set keyboard**           | Switch keyboard layout by index.                     | `wfctl set keyboard 1`                              |
| **set option**             | Change a config value at runtime.                    | `wfctl set option core/vwidth=4`                    |
| **set view alpha**         | Set window transparency (0.0 to 1.0).                | `wfctl set view alpha 12 0.8`                       |
| **set workspace**          | Switch current workspace by index.                   | `wfctl set workspace 2`                             |
| **status plugin**          | Check if a plugin is currently active.               | `wfctl status plugin alpha`                         |
| **update plugins**         | Rebuild all Git-installed plugins.                   | `wfctl update plugins`                              |
