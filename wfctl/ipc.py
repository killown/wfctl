import configparser
import json
from typing import Optional, List, Dict, Any
from wayfire.ipc import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
from wfctl.utils import (
    format_output, find_dicts_with_value,
    workspace_to_coordinates, find_device_id,
    enable_plugin, disable_plugin,
    status_plugin, install_wayfire_plugin
)

# Initialize WayfireSocket and WayfireUtils
sock = WayfireSocket()
utils = WayfireUtils(sock)

# Initialize configparser and load configuration
config = configparser.ConfigParser()
config.read('wayfire_config.ini')

def extract_from_dict(data: Dict[str, Any], command: str, max_len: int) -> Optional[Any]:
    """Extract value from dictionary based on command."""
    key = command.split()
    if len(key) > max_len:
        return data.get(key[-1], "Key not found")
    return None

def handle_list_views(command: str) -> None:
    """Handle the 'list views' command."""
    views = sock.list_views()
    parts = command.split()
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

    formatted_output = json.dumps(views, indent=4)
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
        if value.startswith('-'):
            return value[1:].isdigit() and len(value) > 1  # Ensure that there's at least one digit after '-'
        return value.isdigit()

    def exclude_focused_view(views: Optional[List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Exclude the focused view from the list of views."""
        if views is None:
            return []
        focused_view = sock.get_focused_view()
        return [view for view in views if view != focused_view]

    def format_find_views_output(value: Any, key: Optional[str] = None) -> str:
        """Format the output from utils.find_views and filter out the focused view."""
        # Convert value to integer if it is numeric
        if is_numeric(value) or "-" in value:
            value = int(value)

        views = utils.find_views(value, key)
        views = exclude_focused_view(views)
        return json.dumps(views, indent=4) if views else json.dumps([])

    parts = command.split()
    if len(parts) == 3:
        value = parts[2]
        key = None
        print(format_find_views_output(value, key))  # Pass only value
    elif len(parts) == 4:
        value = parts[2]
        key = parts[3]
        print(format_find_views_output(value, key))  # Pass value and key
    else:
        print("Error: Invalid command format.")

def handle_set_workspace(command: str) -> None:
    """Handle the 'set workspace' command."""
    try:
        workspace_number = int(command.split()[-1])
        grid_width = sock.get_focused_output()["workspace"]["grid_width"]
        coords = workspace_to_coordinates(workspace_number, grid_width)
        sock.set_workspace(coords['x'], coords['y'])
    except ValueError:
        print("Error: Invalid workspace number.")
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
        utils.set_view_maximized(id )
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
            opt, value = option.split(":")
            all_options[opt] = value
        except ValueError:
            print(f"Error: Invalid option format '{option}'.")
    sock.set_option_values(all_options)

def handle_get_keyboard() -> None:
    """Handle the 'get keyboard' command."""
    layout = sock.get_option_value("input/xkb_layout")
    variant = sock.get_option_value("input/xkb_variant")
    print(f"Layout: {layout}, Variant: {variant}")

def handle_list_plugins(command: str) -> None:
    """Handle the 'list plugins' command."""
    plugins = utils.list_plugins()
    print(json.dumps(plugins, indent=4))

def handle_enable_plugin(command: str) -> None:
    """Handle the 'enable plugin' command."""
    parts = command.split()
    plugin_name = parts[2]
    enable_plugin(plugin_name)

def handle_disable_plugin(command: str) -> None:
    """Handle the 'disable plugin' command."""
    parts = command.split()
    plugin_name = parts[2]
    disable_plugin(plugin_name)

def handle_status_plugin(command: str) -> None:
    """Handle the 'status plugin' command."""
    parts = command.split()
    plugin_name = parts[2]
    status = status_plugin(plugin_name)
    print(status)

def handle_install_plugin(command: str) -> None:
    """Handle the 'install plugin' command."""
    parts = command.split()
    plugin_url = parts[2]
    install_wayfire_plugin(plugin_url)

def wayfire_commands(command: str) -> None:
    """Process Wayfire commands."""
    
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
        "get keyboard": handle_get_keyboard,
        "list plugins": handle_list_plugins,
        "enable plugin": handle_enable_plugin,
        "disable plugin": handle_disable_plugin,
        "status plugin": handle_status_plugin,
        "install plugin": handle_install_plugin
    }

    command_parts = command.split()
    if not command_parts:
        print("Error: No command provided.")
        return

    # Extract the command key
    command_key = ' '.join(command_parts[:2])
    if command_key in command_map:
        command_map[command_key](command)
    else:
        print("Error: Command not recognized.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        wayfire_commands(' '.join(sys.argv[1:]))
    else:
        print("Usage: python script.py <command>")



