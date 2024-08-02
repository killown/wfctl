from wayfire.ipc import WayfireSocket
from wayfire.extra.ipc_utils import WayfireUtils
import json
from wfctl.utils import workspace_to_coordinates
sock = WayfireSocket()
utils = WayfireUtils(sock)


def wayfire_commands(command):
    if command == "list views":
        s = sock.list_views()
        formatted_output = json.dumps(s, indent=4)
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

    if "set fullscreen" == command:
        utils.fullscreen_focused()

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
        








