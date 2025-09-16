import configparser
import json
import sys
import inspect
import subprocess
import os
import re
import tempfile
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


def handle_install_plugin(command: str) -> None:
    """
    Handle the 'install plugin' command.
    Installs plugin(s) from a given GitHub repository URL.
    Optionally, specify a plugin name to target a specific subdirectory.
    The repository is cloned into a unique temporary directory and cleaned up afterward.
    Examples:
        wfctl install plugin https://github.com/killown/wayfire-plugins hide-view
        wfctl install plugin https://github.com/killown/wayfire-plugins
    """
    parts = command.split()
    if len(parts) < 3:
        print("Error: Please provide a GitHub repository URL.")
        return

    repo_url = parts[2]
    plugin_name = parts[3] if len(parts) > 3 else None

    # Define the user's local installation root
    home_dir = os.path.expanduser("~")
    local_install_root = os.path.join(home_dir, ".local")

    # The build directory (will be relative to each meson project dir)
    build_dir = "build"

    # Create a unique temporary directory for cloning
    with tempfile.TemporaryDirectory(prefix="wfctl_", dir="/tmp") as tmp_dir:
        print(f"Created temporary directory: {tmp_dir}")

        try:
            clone_path = os.path.join(tmp_dir, "repo_clone")
            print(f"Cloning repository: {repo_url} into {clone_path}")
            subprocess.run(["git", "clone", repo_url, clone_path], check=True)

            project_dirs = []

            if plugin_name:
                # User specified a plugin name, search for that exact directory
                print(f"Searching for plugin directory: {plugin_name}")
                specific_dir = find_specific_plugin_directory(clone_path, plugin_name)
                if specific_dir:
                    project_dirs = [specific_dir]
                    print(f"Found plugin directory: {specific_dir}")
                else:
                    print(
                        f"Error: Could not find a directory named '{plugin_name}' containing a meson.build file."
                    )
                    return
            else:
                # No plugin name specified, find all Wayfire plugin projects
                project_dirs = find_wayfire_plugin_directories(clone_path)
                if not project_dirs:
                    print("Error: No Wayfire plugin projects found in the repository.")
                    return

                print(f"Found {len(project_dirs)} Wayfire plugin project(s):")
                for d in project_dirs:
                    print(f"  - {d}")

            # Install each identified project directory
            for project_dir in project_dirs:
                print(f"\n--- Installing plugin project from: {project_dir} ---")
                original_dir = os.getcwd()
                try:
                    os.chdir(project_dir)

                    print("Configuring build with Meson...")
                    # Configure Meson with the user's local prefix
                    meson_cmd = [
                        "meson",
                        "setup",
                        build_dir,
                        f"--prefix={local_install_root}",
                        "--buildtype=release",
                    ]
                    subprocess.run(meson_cmd, check=True)

                    print("Compiling with Ninja...")
                    subprocess.run(["ninja", "-C", build_dir], check=True)

                    print("Installing...")
                    env = os.environ.copy()
                    env["DESTDIR"] = ""

                    subprocess.run(
                        ["ninja", "-C", build_dir, "install"], env=env, check=True
                    )

                    print(
                        f"Plugin project installed successfully to {local_install_root}"
                    )

                except subprocess.CalledProcessError as e:
                    print(f"Installation failed for {project_dir}: {e}")
                except Exception as e:
                    print(f"An unexpected error occurred for {project_dir}: {e}")
                finally:
                    os.chdir(original_dir)

            print("\nAll plugin projects installed successfully.")
            print("You may need to restart Wayfire for it to detect the new plugins.")
            print("To enable a specific plugin, use: wfctl enable plugin <plugin_name>")

        except subprocess.CalledProcessError as e:
            print(f"Installation failed during step: {e.cmd}")
            print(f"Return code: {e.returncode}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            print(f"Temporary directory {tmp_dir} has been removed.")


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


# Define command mapping to corresponding handler functions
command_map = {
    "list views": handle_list_views,
    "list outputs": handle_list_outputs,
    "search views": handle_search_views,
    "set workspace": handle_set_workspace,
    "get focused output": handle_get_focused_output,
    "get focused view": handle_get_focused_view,
    "get focused workspace": handle_get_focused_workspace,
    "next workspace": handle_next_workspace,
    "fullscreen view": handle_fullscreen_view,
    "get view": handle_get_view,
    "resize view": handle_resize_view,
    "move view": handle_move_view,
    "close view": handle_close_view,
    "minimize view": handle_minimize_view,
    "maximize view": handle_maximize_view,
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
