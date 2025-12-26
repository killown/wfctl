import configparser
import json
import sys
import inspect
import subprocess
import os
import re
import tempfile
from datetime import datetime
from typing import Optional, List, Dict, Any
from wayfire import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
from wfctl.utils import (
    find_dicts_with_value,
    find_device_id,
    enable_plugin,
    disable_plugin,
    status_plugin,
)

sock = WayfireSocket()
utils = WayfireUtils(sock)

config = configparser.ConfigParser()
config.read("wayfire_config.ini")


def extract_from_dict(
    data: Dict[str, Any], command: str, max_len: int
) -> Optional[Any]:
    """Extract value from dictionary based on command."""
    key = command.split()
    if len(key) > max_len:
        return data.get(key[-1], "Key not found")
    return None


def handle_list_views() -> None:
    """Handle the 'list views' command."""
    views = sock.list_views()
    parts = sys.argv[1:]
    if len(parts) > 2:
        value = parts[-1]
        if value.isdigit():
            print("Error: Integer value is not allowed for filtering.")
        else:
            result = find_dicts_with_value(views, value)
            if result:
                views = result
                focused_id = sock.get_focused_view()["id"]
                views = [view for view in views if view["id"] != focused_id]

    formatted_output = json.dumps(views, indent=4, ensure_ascii=False)
    print(formatted_output)


def handle_list_outputs() -> None:
    """Handle the 'list outputs' command."""
    s = sock.list_outputs()
    formatted_output = json.dumps(s, indent=4)
    print(formatted_output)


def handle_search_views(command: str) -> None:
    """Handle the 'search views' command."""

    def is_numeric(value: str) -> bool:
        """Check if a string represents a numeric value (including negative numbers)."""
        if value.startswith("-"):
            return value[1:].isdigit() and len(value) > 1
        return value.isdigit()

    def exclude_focused_view(
        views: Optional[List[Dict[str, Any]]],
    ) -> List[Dict[str, Any]]:
        """Exclude the focused view from the list of views."""
        if views is None:
            return []
        focused_view = sock.get_focused_view()
        return [view for view in views if view != focused_view]

    def format_find_views_output(value: Any, key: Optional[str] = None) -> str:
        """Format the output from utils.find_views and filter out the focused view."""
        if is_numeric(value) or "-" in value:
            value = int(value)

        views = utils.find_views(value, key)
        views = exclude_focused_view(views)
        return json.dumps(views, indent=4) if views else json.dumps([])

    parts = command.split()
    if len(parts) == 3:
        value = parts[2]
        key = None
        print(format_find_views_output(value, key))
    elif len(parts) == 4:
        value = parts[2]
        key = parts[3]
        print(format_find_views_output(value, key))
    else:
        print("Error: Invalid command format.")


def handle_set_workspace(command: str) -> None:
    """Handle the 'set workspace' command."""
    try:
        workspace_number = int(sys.argv[1:][-1])
        x, y = utils._total_workspaces()[workspace_number]
        sock.set_workspace(x, y)
    except Exception as e:
        print(f"Error: {e}")


def handle_get_focused_output(command: str) -> None:
    """Handle the 'get focused output' command."""
    s = sock.get_focused_output()
    key = extract_from_dict(s, command, 3)
    if key:
        print(key)
    else:
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)


def handle_get_focused_view(command: str) -> None:
    """Handle the 'get focused view' command."""
    s = sock.get_focused_view()
    key = extract_from_dict(s, command, 3)
    if key:
        print(key)
    else:
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)


def handle_get_focused_workspace() -> None:
    """Handle the 'get focused workspace' command."""
    s = utils.get_active_workspace_number()
    print(s)


def handle_next_workspace() -> None:
    """Handle the 'next workspace' command."""
    utils.go_next_workspace()


def handle_fullscreen_view(command: str) -> None:
    """Handle the 'fullscreen view' command."""
    try:
        parts = command.split()
        id = int(parts[2])
        state = parts[-1] == "true"
        sock.set_view_fullscreen(id, state)
    except ValueError:
        print("Error: Invalid view ID or state.")
    except Exception as e:
        print(f"Error: {e}")


def is_wayfire_plugin_project(meson_build_path: str) -> bool:
    """
    Analyze a meson.build file to determine if it's for a Wayfire plugin project.
    Looks for indicators like 'dependency('wayfire')' or '-DWAYFIRE_PLUGIN'.
    """
    try:
        with open(meson_build_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Look for key indicators
        indicators = [
            r"dependency\s*\(\s*['\"]wayfire['\"]",
            r"add_project_arguments\s*\(\s*\[[^]]*['\"]-DWAYFIRE_PLUGIN['\"]",
        ]

        for pattern in indicators:
            if re.search(pattern, content, re.IGNORECASE):
                return True

        return False
    except Exception:
        # If we can't read or parse the file, assume it's not a Wayfire plugin
        return False


def find_specific_plugin_directory(root_path: str, plugin_name: str) -> str:
    """
    Recursively search for a directory with the exact name `plugin_name` that contains a meson.build file.
    Returns the path to the directory, or None if not found.
    """
    for dirpath, dirnames, filenames in os.walk(root_path):
        if os.path.basename(dirpath) == plugin_name and "meson.build" in filenames:
            return dirpath
    return None


def find_wayfire_plugin_directories(root_path: str) -> list:
    """
    Recursively search for directories containing a meson.build file that defines a Wayfire plugin project.
    Returns a list of directory paths.
    """
    plugin_dirs = []

    for dirpath, dirnames, filenames in os.walk(root_path):
        if "meson.build" in filenames:
            meson_path = os.path.join(dirpath, "meson.build")
            if is_wayfire_plugin_project(meson_path):
                plugin_dirs.append(dirpath)

    return plugin_dirs


def record_plugin_metadata(plugin_name: str, repo_url: str, install_root: str) -> None:
    """
    Records installation details to a JSON file for future management.

    This function creates a manifest in ~/.local/share/wayfire/installed-plugins/
    containing the source URL, installation date, and filesystem prefix.
    """
    registry_dir = os.path.expanduser("~/.local/share/wayfire/installed-plugins")
    os.makedirs(registry_dir, exist_ok=True)

    metadata_path = os.path.join(registry_dir, f"{plugin_name}.json")

    payload = {
        "name": plugin_name,
        "source": repo_url,
        "install_date": datetime.now().isoformat(),
        "prefix": install_root,
        "managed_by": "wfctl",
    }

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=4)


def _install_from_source(
    repo_url: str, plugin_name: str, local_install_root: str, local_metadata_dir: str
) -> None:
    """
    Core logic to clone, patch, build, and install a Wayfire plugin.

    This is shared between 'install' and 'update' commands to ensure consistent
    build environments and patching logic.
    """
    build_dir = "build"

    with tempfile.TemporaryDirectory(prefix="wfctl_", dir="/tmp") as tmp_dir:
        clone_path = os.path.join(tmp_dir, "repo_clone")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, clone_path], check=True
        )

        # Determine which directories to build
        specific_dir = find_specific_plugin_directory(clone_path, plugin_name)
        project_dirs = (
            [specific_dir]
            if specific_dir
            else find_wayfire_plugin_directories(clone_path)
        )

        if not project_dirs:
            print(f"Warning: No valid Wayfire plugin project found for {plugin_name}")
            return

        for project_dir in project_dirs:
            original_dir = os.getcwd()
            try:
                os.chdir(project_dir)

                # --- Patch metadata/meson.build ---
                metadata_src_dir = os.path.join(project_dir, "metadata")
                meson_build_file = os.path.join(metadata_src_dir, "meson.build")

                if os.path.exists(meson_build_file):
                    with open(meson_build_file, "r") as f:
                        lines = f.readlines()
                    lines = [line for line in lines if "install_data" not in line]

                    xml_files = [
                        f for f in os.listdir(metadata_src_dir) if f.endswith(".xml")
                    ]
                    if xml_files:
                        xml_file = xml_files[0]
                        lines.append(
                            f"install_data('{xml_file}', install_dir: '{local_metadata_dir}')\n"
                        )
                        with open(meson_build_file, "w") as f:
                            f.writelines(lines)

                # --- Build and Install ---
                meson_cmd = [
                    "meson",
                    "setup",
                    build_dir,
                    f"--prefix={local_install_root}",
                    "--libdir=lib",
                    "--datadir=share",
                    "--buildtype=release",
                ]
                subprocess.run(meson_cmd, check=True)
                subprocess.run(["ninja", "-C", build_dir], check=True)
                subprocess.run(["ninja", "-C", build_dir, "install"], check=True)

                # --- Update Registry ---
                record_plugin_metadata(plugin_name, repo_url, local_install_root)
            finally:
                os.chdir(original_dir)


def handle_update_plugins() -> None:
    """
    Handle the 'update plugins' command.

    Iterates through all JSON files in the local registry, pulls the latest
    source code from their recorded URLs, and re-installs them.
    """
    registry_dir = os.path.expanduser("~/.local/share/wayfire/installed-plugins")
    if not os.path.exists(registry_dir):
        print("No plugins installed via wfctl registry found.")
        return

    home_dir = os.path.expanduser("~")
    local_install_root = os.path.join(home_dir, ".local")
    local_metadata_dir = os.path.join(local_install_root, "share/wayfire/metadata")

    for filename in os.listdir(registry_dir):
        if filename.endswith(".json"):
            metadata_path = os.path.join(registry_dir, filename)
            try:
                with open(metadata_path, "r") as f:
                    data = json.load(f)

                plugin_name = data.get("name")
                repo_url = data.get("source")

                if not repo_url:
                    continue

                print(f"--- Updating plugin: {plugin_name} ---")
                _install_from_source(
                    repo_url, plugin_name, local_install_root, local_metadata_dir
                )
                print(f"Successfully updated {plugin_name}\n")

            except Exception as e:
                print(f"Failed to update {filename}: {e}")


def handle_install_plugin(command: str) -> None:
    """Handle the 'install plugin' command."""
    parts = command.split()
    if len(parts) < 3:
        print("Error: Please provide a GitHub repository URL.")
        return

    repo_url = parts[2]
    plugin_name = (
        parts[3] if len(parts) > 3 else repo_url.split("/")[-1].replace(".git", "")
    )

    home_dir = os.path.expanduser("~")
    local_install_root = os.path.join(home_dir, ".local")
    local_metadata_dir = os.path.join(local_install_root, "share/wayfire/metadata")

    os.makedirs(local_metadata_dir, exist_ok=True)

    try:
        _install_from_source(
            repo_url, plugin_name, local_install_root, local_metadata_dir
        )
        print(f"Installation of {plugin_name} complete.")
    except Exception as e:
        print(f"Installation failed: {e}")


def handle_get_view(command: str) -> None:
    """Handle the 'get view' command."""
    try:
        id = int(command.split()[-1])
        s = sock.get_view(id)
        key = extract_from_dict(s, command, 3)
        if key:
            print(key)
        else:
            formatted_output = json.dumps(s, indent=4)
            print(formatted_output)
    except ValueError:
        print("Error: Invalid view ID.")
    except Exception as e:
        print(f"Error: {e}")


def handle_resize_view(command: str) -> None:
    """Handle the 'resize view' command."""
    try:
        parts = command.split()
        id = int(parts[2])
        width = int(parts[3])
        height = int(parts[4])
        geo = sock.get_view(id)["base-geometry"]
        sock.configure_view(id, geo["x"], geo["y"], width, height)
    except ValueError:
        print("Error: Invalid view ID, width, or height.")
    except Exception as e:
        print(f"Error: {e}")


def handle_move_view(command: str) -> None:
    """Handle the 'move view' command."""
    try:
        parts = command.split()
        id = int(parts[2])
        x = int(parts[3])
        y = int(parts[4])
        geo = sock.get_view(id)["base-geometry"]
        sock.configure_view(id, x, y, geo["width"], geo["height"])
    except ValueError:
        print("Error: Invalid view ID, x, or y.")
    except Exception as e:
        print(f"Error: {e}")


def handle_close_view(command: str) -> None:
    """Handle the 'close view' command."""
    try:
        id = int(command.split()[-1])
        sock.close_view(id)
    except ValueError:
        print("Error: Invalid view ID.")
    except Exception as e:
        print(f"Error: {e}")


def handle_minimize_view(command: str) -> None:
    """Handle the 'minimize view' command."""
    try:
        parts = command.split()
        id = int(parts[2])
        status = parts[3] == "true"
        sock.set_view_minimized(id, status)
    except ValueError:
        print("Error: Invalid view ID or status.")
    except Exception as e:
        print(f"Error: {e}")


def handle_maximize_view(command: str) -> None:
    """Handle the 'maximize view' command."""
    try:
        id = int(command.split()[-1])
        utils.set_view_maximized(id)
    except ValueError:
        print("Error: Invalid view ID.")
    except Exception as e:
        print(f"Error: {e}")


def handle_set_view_alpha(command: str) -> None:
    """Handle the 'set view alpha' command."""
    try:
        parts = command.split()
        id = int(parts[3])
        alpha = float(parts[-1])
        sock.set_view_alpha(id, alpha)
    except ValueError:
        print("Error: Invalid view ID or alpha value.")
    except Exception as e:
        print(f"Error: {e}")


def handle_list_inputs() -> None:
    """Handle the 'list inputs' command."""
    s = sock.list_input_devices()
    formatted_output = json.dumps(s, indent=4)
    print(formatted_output)


def handle_configure_device(command: str) -> None:
    """Handle the 'configure device' command."""
    try:
        parts = command.split()
        status = parts[-1]
        device_id = parts[2]
        status = status == "enable"
        device_id = find_device_id(device_id)
        if device_id:
            sock.configure_input_device(device_id, status)
    except Exception as e:
        print(f"Error: {e}")


def handle_get_option(command: str) -> None:
    """Handle the 'get option' command."""
    option = command.split()[-1]
    value = sock.get_option_value(option)
    print(value)


def handle_set_option(command: str) -> None:
    """Handle the 'set option' command."""
    options = command.split()[2:]
    all_options = {}
    for option in options:
        try:
            opt, val = option.split("=")
            all_options[opt] = val
        except ValueError:
            print(f"Error: Invalid format for option '{option}'")
            return

    for option, value in all_options.items():
        sock.set_option_values(option)
        print(f"Option {option} set to {value}")


def handle_plugin_action(command: str, action: str) -> None:
    """Handle plugin-related actions (enable, disable, status)."""
    plugin_name = command.split()[-1]
    try:
        if action == "enable":
            enable_plugin(plugin_name)
        elif action == "disable":
            disable_plugin(plugin_name)
        elif action == "status":
            print(status_plugin(plugin_name))
    except Exception as e:
        print(f"Error: {e}")


def handle_get_keyboard() -> None:
    """
    Handle the 'get keyboard' command.

    Queries the compositor for possible layouts and the currently active index,
    returning a structured JSON representation of the keyboard state.
    """
    try:
        layout_data = sock.get_keyboard_layout()
        print(json.dumps(layout_data, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")


def handle_set_keyboard(command: str) -> None:
    """
    Handle the 'set keyboard' command.

    Accepts an integer index to switch the active keyboard layout.
    Example: wfctl set keyboard 1
    """
    try:
        parts = command.split()
        if len(parts) < 3:
            print("Error: Please provide a layout index.")
            return

        index = int(parts[2])
        result = sock.set_keyboard_layout(index)

        if result.get("result") == "ok":
            print(f"Keyboard layout changed to index {index}")
        else:
            print(f"Compositor returned an error: {result}")

    except ValueError:
        print("Error: Layout index must be an integer.")
    except Exception as e:
        print(f"Error: {e}")


# Define command mapping to corresponding handler functions
command_map = {
    "list views": handle_list_views,
    "list outputs": handle_list_outputs,
    "search views": handle_search_views,
    "set workspace": handle_set_workspace,
    "get focused output": handle_get_focused_output,
    "get focused view": handle_get_focused_view,
    "get focused workspace": handle_get_focused_workspace,
    "get keyboard": handle_get_keyboard,
    "set keyboard": handle_set_keyboard,
    "next workspace": handle_next_workspace,
    "fullscreen view": handle_fullscreen_view,
    "get view": handle_get_view,
    "resize view": handle_resize_view,
    "move view": handle_move_view,
    "close view": handle_close_view,
    "minimize view": handle_minimize_view,
    "maximize view": handle_maximize_view,
    "update plugins": handle_update_plugins,
    "set view alpha": handle_set_view_alpha,
    "list inputs": handle_list_inputs,
    "configure device": handle_configure_device,
    "get option": handle_get_option,
    "set option": handle_set_option,
    "enable plugin": lambda command: handle_plugin_action(command, "enable"),
    "disable plugin": lambda command: handle_plugin_action(command, "disable"),
    "status plugin": lambda command: handle_plugin_action(command, "status"),
    "install plugin": handle_install_plugin,
}


def has_arguments(func):
    """Check if a function has any arguments."""
    signature = inspect.signature(func)
    return len(signature.parameters) > 0


def normalize_command(command: str) -> str:
    """
    Trim surrounding whitespace and collapse runs of whitespace into single spaces.
    Also removes stray \r, tabs, zero-width spaces when possible via split/join.
    """
    if command is None:
        return ""
    # split()/join() removes all whitespace runs (including \r, \t, multiple spaces)
    return " ".join(command.split()).strip()


def find_best_command_key(command: str) -> Optional[str]:
    """
    Return the best-matching key from command_map for the given command string.
    Matching rules:
      - command == key, OR command starts with key + " "
      - among matches, return the longest key (most specific)
    """
    matches = [
        k for k in command_map.keys() if command == k or command.startswith(k + " ")
    ]
    if not matches:
        return None
    # choose the longest (most specific) match
    return max(matches, key=len)


def execute_command(command: str) -> None:
    """Execute a command based on user input with safer matching and normalized input."""
    command = normalize_command(command)
    if not command:
        print("Error: empty command")
        return

    key = find_best_command_key(command)
    if key is None:
        print(f"Error: Unknown command '{command}'")
        return

    exec_function = command_map[key]

    # print(f"DEBUG: matched key={repr(key)} for command={repr(command)}")

    if has_arguments(exec_function):
        exec_function(command)
    else:
        exec_function()
