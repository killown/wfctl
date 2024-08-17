import configparser
from wayfire.ipc import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
import json
from wfctl.utils import (
    format_output, find_dicts_with_value, 
    workspace_to_coordinates, find_device_id, 
    set_output, enable_plugin, disable_plugin, 
    status_plugin, install_wayfire_plugin
)

# Initialize WayfireSocket and WayfireUtils
sock = WayfireSocket()
utils = WayfireUtils(sock)

# Initialize configparser and load configuration
config = configparser.ConfigParser()
config.read('wayfire_config.ini')

# Helper functions
def print_output(data, format="fancy_grid"):
    if "-f" in data:
        return format_output(str(data), format)
    else:
        return data

def extract_from_dict(s, command, max_len):
    key = command.split()
    if len(key) > max_len:
        return s[key[-1]]

# Main command processing function
def wayfire_commands(command):
    if "list views" in command:
        views = sock.list_views()
        value = command.split()[-1]
        if len(command.split()) > 2:
            result = find_dicts_with_value(views, value)
            if result:
                views = result
                focused_id = sock.get_focused_view()["id"]
                views = [view for view in views if view["id"] != focused_id]

        formatted_output = json.dumps(views, indent=4)
        print(formatted_output)

    if command == "list outputs":
        s = sock.list_outputs()
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "set workspace" in command:
        workspace_number = int(command.split()[-1])
        grid_width = sock.get_focused_output()["workspace"]["grid_width"]
        coordinates = workspace_to_coordinates(workspace_number, grid_width)
        sock.set_workspace(coordinates)
    
    if "get focused output" in command:
        s = sock.get_focused_output()
        key = extract_from_dict(s, command, 3)
        if key:
            print(key)
            return
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "get focused view" in command:
        s = sock.get_focused_view()
        key = extract_from_dict(s, command, 3)
        if key:
            print(key)
            return
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "get focused workspace" in command:
        s = utils.get_active_workspace_number()
        print(s)

    if "next workspace" in command:
        utils.go_next_workspace()

    if "fullscreen view" in command:
        id = int(command.split()[2])
        state = command.split()[-1]
        sock.set_view_fullscreen(id, state)

    if "get view" in command:
        id = int(command.split()[2])
        try:
            s = sock.get_view(id)
        except:
            print("view not found")
            return
        key = extract_from_dict(s, command, 3)
        if key:
            print(key)
            return
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)

    if "resize view" in command:
        cmd = command.split()
        id = int(cmd[2])
        width = int(cmd[3])
        height = int(cmd[4])
        geo = sock.get_view(id)["base-geometry"]
        x = geo["x"]
        y = geo["y"]
        sock.configure_view(id, x, y, width, height)

    if "move view" in command:
        cmd = command.split()
        id = int(cmd[2])
        x = int(cmd[3])
        y = int(cmd[4])
        geo = sock.get_view(id)["base-geometry"]
        width = geo["width"]
        height = geo["height"]
        sock.configure_view(id, x, y, width, height)

    if "close view" in command:
        id = int(command.split()[-1])
        sock.close_view(id)

    if "minimize view" in command:
        id = int(command.split()[2])
        status = command.split()[3]
        status = True if status == "true" else False
        sock.set_view_minimized(id, status)

    if "maximize view" in command:
        id = int(command.split()[-1])
        utils.maximize(id)

    if "set view alpha" in command:
        id = int(command.split()[3])
        alpha = float(command.split()[-1])
        sock.set_view_alpha(id, alpha)

    if "list inputs" in command:
        s = sock.list_input_devices()
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)

    if "configure device" in command:
        status = command.split()[-1]
        device_id = command.split()[2]
        status = True if status == "enable" else False
        if isinstance(status, bool):
            device_id = find_device_id(device_id)
            sock.configure_input_device(device_id, status)

    if "get option" in command:
        option = command.split()[-1]
        value = sock.get_option_value(option)
        print(value)

    if "set option" in command:
        options = command.split()[2:]
        all_options = {}
        for option in options:
            opt, value = option.split(":")
            all_options[opt] = value
        sock.set_option_values(all_options)

    if "get keyboard" in command:
        layout = sock.get_option_value("input/xkb_layout")
        variant = sock.get_option_value("input/xkb_variant")
        model = sock.get_option_value("input/xkb_model")
        options = sock.get_option_value("input/xkb_options")
        xkb = {
            "layout": layout["value"], 
            "variant": variant["value"], 
            "model": model["value"], 
            "options": options["value"]
        }
        xkb = json.dumps(xkb, indent=4)
        print(xkb)

    if "enable plugin" in command:
        plugin_name = command.split()[-1]
        enable_plugin(plugin_name)
        
    if "disable plugin" in command:
        plugin_name = command.split()[-1]
        disable_plugin(plugin_name)

    if "reload plugin" in command:
        plugin_name = command.split()[-1]
        disable_plugin(plugin_name)
        enable_plugin(plugin_name)

    if "status plugin" in command:
        plugin_name = command.split()[-1]
        status_plugin(plugin_name)

    if "install plugin" in command:
        plugin_url = command.split()[-1]
        install_wayfire_plugin(plugin_url)

    if "set output" in command:
        output_name = command.split()[2]
        status = command.split()[-1]
        set_output(output_name, status)

    if "set keyboard" in command:
        k = " ".join(command.split()[2:])
        xkb_layout = None 
        xkb_variant = None 
        xkb_model = None 
        xkb_options = None

        if "layout:" in command:
            xkb_layout = k.split("layout:")[1].split()[0]
        if "variant:" in command:
            xkb_variant = k.split("variant:")[1].split()[0]
        if "model:" in command:
            xkb_model = k.split("model:")[1].split()[0]
        if "options:" in command:
            xkb_options = k.split("options:")[1].split()[0]

        if xkb_layout:
            sock.set_option_values({"input/xkb_layout": xkb_layout})
        if xkb_variant:
            sock.set_option_values({"input/xkb_variant": xkb_variant})
        if xkb_model:
            sock.set_option_values({"input/xkb_model": xkb_model})
        if xkb_options:
            sock.set_option_values({"input/xkb_options": xkb_options})

# Watch Wayfire events
def watch_events():
    sock.watch()

    while True:
        msg = sock.read_message()
        print(msg)

# Example of how to use configuration options
def main():
    # Example configuration usage
    default_output = config.get('General', 'default_output', fallback='fancy_grid')
    default_command = config.get('Commands', 'default_command', fallback='list views')

    # Execute the default command with the default output format
    wayfire_commands(default_command, format=default_output)

if __name__ == "__main__":
    main()

