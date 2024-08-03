from wayfire.ipc import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
import json
from wfctl.utils import format_output, workspace_to_coordinates, find_device_id, format_output
sock = WayfireSocket()
utils = WayfireUtils(sock)

def print_output(data, format="fancy_grid"):
    if "-f" in data:
        return format_output(str(data), format)
    else:
        return data

def wayfire_commands(command, format=None):
    if "list views" in command:
        s = sock.list_views()
        formatted_output = json.dumps(s, indent=4)
        if format is not None:
            print(format_output(str(formatted_output)))
        else:
            print(formatted_output)
    
    if command == "list outputs":
        s = sock.list_outputs()
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "switch workspace" in command:
        workspace_number = int(command.split()[-1])
        grid_width = sock.get_focused_output()["workspace"]["grid_width"]
        coordinates = workspace_to_coordinates(workspace_number, grid_width)
        sock.set_workspace(coordinates)
    
    if "get focused output" in command:
        s = sock.get_focused_output()
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "get focused view" in command:
        s = sock.get_focused_view()
        formatted_output = json.dumps(s, indent=4)
        print(formatted_output)
    
    if "get focused workspace" in command:
        s = utils.get_active_workspace_number()
        print(s)

    if "next workspace" in command:
        utils.go_next_workspace()

    if "fullscreen view" in command:
        id = int(command.split()[-1])
        sock.set_view_fullscreen(id)

    if "get view info" in command:
        id = int(command.split()[-1])
        try:
            s = sock.get_view(id)
        except:
            print("view not found")
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
        if status == "true":
            status = True
        if status == "false":
            status = False
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
        print(device_id)
        if status == "enable":
            status = True
        if status == "disable":
            status = False
        if type(status) is bool:
            device_id = find_device_id(device_id)
            print(type(device_id))
            sock.configure_input_device(device_id, status)

    if "get option" in command:
        option = command.split()[-1]
        value = sock.get_option_value(option)
        print(value)


    if "set option" in command:
        options = command.split()[2:]
        all_options = {}
        for option in options:
            opt = option.split(":")[0]
            value = option.split(":")[-1]
            all_options[opt] = value
        print(all_options)
        sock.set_option_values(all_options)


def watch_events():
    sock.watch()

    while True:
        msg = sock.read_message()
        print(msg)







