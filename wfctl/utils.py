from wayfire.ipc import WayfireSocket 
import json
from tabulate import tabulate
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

def flatten_json(data, parent_key=''):
    items = []
    for k, v in data.items():
        new_key = f"{parent_key}.{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_json(v, new_key).items())
        else:
            items.append((new_key, v))
    return dict(items)

def format_output(json_data, tablefmt="fancy_grid"):
    data = json.loads(json_data)
    flat_data = flatten_json(data)
    # Prepare data for tabulate
    table_data = [[k, v] for k, v in flat_data.items()]
    headers = ["Key", "Value"]
    table = tabulate(table_data, headers=headers, tablefmt=tablefmt)
    return table


def disable_plugin(plugin_name):
    plugins = sock.get_option_value("core/plugins")["value"]
    p = " ".join([i for i in plugins.split() if plugin_name not in i])
    sock.set_option_values({"core/plugins": p})

def enable_plugin(plugin_name):
    plugins = sock.get_option_value("core/plugins")["value"]
    p = plugins + " " +  plugin_name
    sock.set_option_values({"core/plugins": p})
