from wayfire.ipc import WayfireSocket 
sock = WayfireSocket()

def workspace_to_coordinates(workspace_number, grid_width):
    """
    Convert a workspace number to coordinates in the grid.
    
    :param workspace_number: Workspace number (1-based)
    :param grid_width: Number of columns in the grid
    :return: Dictionary with x and y coordinates (0-based)
    """
    # Convert workspace number to 0-based index
    index = workspace_number - 1
    x = index % grid_width
    y = index // grid_width
    return {"x": x, "y": y}

def find_device_id(name_or_id_or_type):
    sock = WayfireSocket()
    devices = sock.list_input_devices()
    for dev in devices:
        if dev['name'] == name_or_id_or_type or str(dev['id']) == name_or_id_or_type or dev['type'] == name_or_id_or_type:
            return int(dev['id'])
    return None
