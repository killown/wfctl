from wayfire.ipc import WayfireSocket 
import json
from tabulate import tabulate
import os 
import tempfile
import subprocess

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

def set_output(output_name, status):
    method = "output:{}/mode".format(output_name)
    if status == "on":
        status = "auto"
    sock.set_option_values({method:status})

def status_plugin(plugin_name):
    status = plugin_name in sock.get_option_value("core/plugins")["value"].split()
    if status:
        print("plugin enabled")
    else:
        print("plugin disabled")

def install_wayfire_plugin(github_url):
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_name = github_url.rstrip('/').split('/')[-1]
        repo_dir = os.path.join(temp_dir, repo_name)
        subprocess.run(['git', 'clone', github_url, repo_dir], check=True)
        os.chdir(repo_dir)
        os.environ['PKG_CONFIG_PATH'] = '/usr/lib/wlroots/pkgconfig'
        subprocess.run(['meson', 'setup', 'build', '--prefix=/usr'], check=True)
        subprocess.run(['sudo', 'ninja', '-C', 'build', 'install'], check=True)
        print("Plugin installed successfully.")

def find_dicts_with_value(dict_list, value):
    matches = []
    for d in dict_list:
        # Check top-level values
        if any(value in str(v) for v in d.values()):
            matches.append(d)
        # Check nested dictionaries
        for v in d.values():
            if isinstance(v, dict) and any(value in str(sub_v) for sub_v in v.values()):
                matches.append(d)
    return matches
