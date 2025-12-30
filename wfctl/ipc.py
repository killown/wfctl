import configparser
import json
import sys
import inspect
import subprocess
import os
import re
import tempfile
import xml.etree.ElementTree as ET
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

    This handles the full lifecycle from git ingestion to binary deployment,
    including a destructive patch of the metadata build configuration.
    """
    build_dir: str = "build"

    with tempfile.TemporaryDirectory(prefix="wfctl_", dir="/tmp") as tmp_dir:
        clone_path: str = os.path.join(tmp_dir, "repo_clone")
        subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, clone_path], check=True
        )

        specific_dir: str | None = find_specific_plugin_directory(
            clone_path, plugin_name
        )
        project_dirs: list[str] = (
            [specific_dir]
            if specific_dir
            else find_wayfire_plugin_directories(clone_path)
        )

        if not project_dirs:
            print(f"Warning: No valid Wayfire plugin project found for {plugin_name}")
            return

        for project_dir in project_dirs:
            original_dir: str = os.getcwd()
            try:
                os.chdir(project_dir)

                # --- Patch metadata/meson.build ---
                # We identify the target metadata directory and the build definition
                metadata_src_dir: str = os.path.join(project_dir, "metadata")
                meson_build_file: str = os.path.join(metadata_src_dir, "meson.build")

                if os.path.exists(metadata_src_dir):
                    xml_files: list[str] = [
                        f for f in os.listdir(metadata_src_dir) if f.endswith(".xml")
                    ]

                    if xml_files:
                        xml_file: str = xml_files[0]
                        # Destructive overwrite: ignores existing content and applies only our patch.
                        with open(meson_build_file, "w", encoding="utf-8") as f:
                            f.write(
                                f"install_data('{xml_file}', install_dir: '{local_metadata_dir}')\n"
                            )

                # --- Build and Install ---
                meson_cmd: list[str] = [
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
    Uses hardcoded ~/.local logic for metadata.
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
    plugin_path_env = os.getenv("WAYFIRE_PLUGIN_PATH")

    if not plugin_path_env:
        print("Error: WAYFIRE_PLUGIN_PATH environment variable is not set.")
        print("Plugins cannot be installed without a defined target path.")
        sys.exit(1)

    target_plugin_dir = plugin_path_env.split(":")[0]

    local_install_root = os.path.abspath(os.path.join(target_plugin_dir, "../.."))
    local_metadata_dir = os.path.join(local_install_root, "share/wayfire/metadata")

    parts = command.split()
    if len(parts) < 3:
        print("Error: Please provide a GitHub repository URL.")
        return

    repo_url = parts[2]
    plugin_name = (
        parts[3] if len(parts) > 3 else repo_url.split("/")[-1].replace(".git", "")
    )

    os.makedirs(local_metadata_dir, exist_ok=True)

    try:
        _install_from_source(
            repo_url, plugin_name, local_install_root, local_metadata_dir
        )
        print(f"Installation of {plugin_name} complete.")
        print(f"Binary: {target_plugin_dir}")
        print(f"Metadata: {local_metadata_dir}")
    except Exception as e:
        print(f"Installation failed: {e}")


def handle_uninstall_plugin() -> None:
    """
    Handle the 'uninstall plugin {name}' command.

    Locates and removes the .so binary, .xml metadata, and the installation
    record JSON from the .local/share/wayfire/installed-plugins/ directory.
    Prevents accidental removal of core system modules and provides a
    confirmation prompt before deletion.

    Returns:
        None
    """
    import os
    import sys

    args: list[str] = sys.argv[1:]
    if len(args) < 3:
        print("Error: Usage: wfctl uninstall plugin {plugin_name}")
        return

    plugin_name: str = args[2]
    internal_modules: set[str] = {"core", "input", "workarounds", "ipc", "stipc"}

    if plugin_name in internal_modules:
        print(f"Error: '{plugin_name}' is a core module and cannot be uninstalled.")
        return

    home: str = os.path.expanduser("~")
    plugin_path_env: str = os.getenv("WAYFIRE_PLUGIN_PATH", "")

    raw_lib_paths: list[str] = [p for p in plugin_path_env.split(":") if p] + [
        "/usr/lib/wayfire",
        "/usr/local/lib/wayfire",
        os.path.join(home, ".local/lib/wayfire"),
    ]

    lib_paths: list[str] = list(
        set(os.path.abspath(p) for p in raw_lib_paths if os.path.isdir(p))
    )

    raw_meta_paths: list[str] = [
        "/usr/share/wayfire/metadata",
        "/usr/local/share/wayfire/metadata",
        os.path.join(home, ".local/share/wayfire/metadata"),
    ]

    meta_paths: list[str] = list(
        set(os.path.abspath(p) for p in raw_meta_paths if os.path.isdir(p))
    )

    installed_record_dir: str = os.path.join(
        home, ".local/share/wayfire/installed-plugins"
    )
    files_to_remove: list[str] = []

    binary_name: str = f"lib{plugin_name}.so"
    for lb in lib_paths:
        full_path: str = os.path.join(lb, binary_name)
        if os.path.exists(full_path) and full_path not in files_to_remove:
            files_to_remove.append(full_path)

    xml_name: str = f"{plugin_name}.xml"
    for mp in meta_paths:
        full_path: str = os.path.join(mp, xml_name)
        if os.path.exists(full_path) and full_path not in files_to_remove:
            files_to_remove.append(full_path)

    record_path: str = os.path.join(installed_record_dir, f"{plugin_name}.json")
    if os.path.exists(record_path):
        files_to_remove.append(record_path)

    config_json: str = os.path.expanduser(f"~/.config/wayfire/{plugin_name}.json")
    if os.path.exists(config_json):
        files_to_remove.append(config_json)

    if not files_to_remove:
        print(f"Error: No artifacts found for plugin '{plugin_name}'.")
        return

    print(f"Found {len(files_to_remove)} artifacts for '{plugin_name}':")
    for f in files_to_remove:
        print(f"  [TARGET] {f}")

    confirm: str = input("\nProceed with uninstallation? (y/N): ").lower()
    if confirm != "y":
        print("Uninstallation aborted.")
        return

    for f in files_to_remove:
        try:
            os.remove(f)
            print(f"Successfully removed: {f}")
        except PermissionError:
            print(f"Permission denied: {f}. Use sudo if required.")
        except Exception as e:
            print(f"Error deleting {f}: {e}")

    print(f"\nUninstallation of '{plugin_name}' complete.")


def handle_check_abi(command: str) -> None:
    """
    Handle 'check abi {path}'
    Example: wfctl check abi /usr/lib/wayfire/libalpha.so
    """
    parts = command.split()
    if len(parts) < 3:
        print("Error: Usage: check abi {path}")
        return

    full_path = parts[2]
    try:
        res = sock.send_json(
            {
                "method": "wayfire/get-plugin-abi-version",
                "data": {"path": full_path},
            }
        )
        # Format and print your ABI result here...
        print(json.dumps(res, indent=4))
    except Exception as e:
        print(f"Error checking ABI: {e}")


def handle_list_plugins() -> None:
    """
    Handle the 'list plugins' command by aggregating and sorting metadata.

    This function performs the following steps:
    1. Resolves metadata and plugin binary paths.
    2. Queries the Wayfire IPC for the currently enabled plugins.
    3. Audits all found .so binaries for ABI compatibility.
    4. Parses XML metadata for descriptions and titles.
    5. Filters out internal core modules.
    6. Sorts the resulting list primarily by state (ENABLED first)
       and secondarily by name.
    7. Outputs a formatted table to stdout.

    Returns:
        None
    """
    import os
    import re

    plugin_path_env: str = os.getenv("WAYFIRE_PLUGIN_PATH", "")
    internal_modules: set[str] = {"core", "input", "workarounds"}

    target_plugin_dir: str = (
        plugin_path_env.split(":")[0]
        if plugin_path_env
        else os.path.expanduser("~/.local/lib/wayfire")
    )
    local_metadata_dir: str = os.path.abspath(
        os.path.join(target_plugin_dir, "../../share/wayfire/metadata")
    )

    metadata_dirs: list[str] = [
        local_metadata_dir,
        "/usr/share/wayfire/metadata",
        "/usr/local/share/wayfire/metadata",
    ]

    enabled_plugins: set[str] = set()
    try:
        plugins_data: dict = sock.get_option_value("core/plugins")
        if isinstance(plugins_data, dict) and "value" in plugins_data:
            enabled_plugins = {
                p.strip() for p in plugins_data["value"].split() if p.strip()
            }
    except Exception:
        pass

    abi_report: dict[str, dict] = {}
    search_paths: list[str] = plugin_path_env.split(":") + [
        "/usr/lib/wayfire",
        "/usr/local/lib/wayfire",
    ]
    for path in search_paths:
        path = os.path.abspath(os.path.expanduser(path))
        if not os.path.isdir(path):
            continue
        for f in os.listdir(path):
            if f.endswith(".so"):
                full_path: str = os.path.join(path, f)
                try:
                    res: dict = sock.send_json(
                        {
                            "method": "wayfire/get-plugin-abi-version",
                            "data": {"path": full_path},
                        }
                    )
                    abi_report[f] = res
                except Exception:
                    continue

    plugin_list: list[dict[str, Any]] = []
    seen_plugins: set[str] = set()

    for m_dir in metadata_dirs:
        if not os.path.isdir(m_dir):
            continue

        for xml_file in os.listdir(m_dir):
            if not xml_file.endswith(".xml"):
                continue

            try:
                with open(os.path.join(m_dir, xml_file), "r", encoding="utf-8") as f:
                    content: str = f.read()

                p_name_match: Optional[re.Match] = re.search(
                    r'<plugin name="([^"]+)">', content
                )
                if not p_name_match:
                    continue

                p_name: str = p_name_match.group(1).strip()

                if p_name in seen_plugins or p_name in internal_modules:
                    continue
                seen_plugins.add(p_name)

                desc_match: Optional[re.Match] = re.search(
                    r"<(?:_|)long>(.*?)</(?:_|)long>", content, re.DOTALL
                )
                desc: str = (
                    desc_match.group(1).strip().replace("\n", " ")
                    if desc_match
                    else "No description"
                )

                is_enabled: bool = p_name in enabled_plugins

                abi: Optional[dict] = abi_report.get(f"lib{p_name}.so")
                version: str = (
                    str(abi.get("plugin_abi_version", "N/A")) if abi else "N/A"
                )
                status: str = (
                    "OK"
                    if (abi and abi.get("compatible"))
                    else ("OUTDATED" if abi else "MISSING")
                )

                plugin_list.append(
                    {
                        "name": p_name,
                        "version": version,
                        "status": status,
                        "state": "ENABLED" if is_enabled else "DISABLED",
                        "description": desc,
                        "is_enabled_bool": is_enabled,
                    }
                )
            except Exception:
                continue

    plugin_list.sort(key=lambda x: (not x["is_enabled_bool"], x["name"]))

    print(
        f"{'PLUGIN':<24} | {'VER':<8} | {'STATUS':<8} | {'STATE':<10} | {'DESCRIPTION'}"
    )
    print("-" * 105)

    for p in plugin_list:
        display_desc: str = (
            (p["description"][:65] + "...")
            if len(p["description"]) > 65
            else p["description"]
        )
        print(
            f"{p['name']:<24} | {p['version']:<8} | {p['status']:<8} | "
            f"{p['state']:<10} | {display_desc}"
        )


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


def handle_list_options(command: str) -> None:
    """
    Parse Wayfire plugin XML and display options including live and default values.

    This function synchronizes static metadata from the filesystem with the
    live state of the compositor.

    Args:
        command: The raw command string, expected format: 'list options <plugin_name>'
    """
    parts = command.split()
    if len(parts) < 3:
        print("Error: Missing plugin name. Usage: wfctl list options <plugin>")
        return

    plugin_name = parts[2]

    search_paths = [
        f"/usr/share/wayfire/metadata/{plugin_name}.xml",
        f"/usr/local/share/wayfire/metadata/{plugin_name}.xml",
        os.path.expanduser(f"~/.local/share/wayfire/metadata/{plugin_name}.xml"),
    ]

    xml_path = next((p for p in search_paths if os.path.exists(p)), None)

    if not xml_path:
        print(f"Error: Metadata for plugin '{plugin_name}' not found.")
        return

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except ET.ParseError as e:
        print(f"Error: Failed to parse XML metadata: {e}")
        return

    plugin = root.find(f".//plugin[@name='{plugin_name}']")
    if plugin is None:
        print(f"Error: Plugin definition for '{plugin_name}' not found in {xml_path}")
        return

    options_data: List[Dict[str, Any]] = []
    for option in plugin.findall(".//option"):
        name = option.get("name", "N/A")
        opt_type = option.get("type", "N/A")
        short_desc = option.findtext("_short", default="No description")
        default_val = option.findtext("default", default="")

        full_option_path = f"{plugin_name}/{name}"
        try:
            live_data = sock.get_option_value(full_option_path)
            current_val = (
                live_data.get("value", "N/A") if isinstance(live_data, dict) else "N/A"
            )
        except Exception:
            current_val = "Error"

        options_data.append(
            {
                "name": name,
                "type": opt_type,
                "default": default_val,
                "current": current_val,
                "description": short_desc,
            }
        )

    render_options_table(plugin_name, options_data)


def render_options_table(plugin_name: str, options: List[Dict[str, Any]]) -> None:
    """
    Renders the options into a high-density table format.
    """
    if not options:
        print(f"No options found for plugin: {plugin_name}")
        return

    headers = ["OPTION", "TYPE", "DEFAULT", "CURRENT", "DESCRIPTION"]
    col_widths = [20, 20, 20, 20, 45]

    print(f"\n[ Configuration for Plugin: {plugin_name} ]")

    # Header
    header_fmt = "".join(f"{headers[i]:<{col_widths[i]}}" for i in range(len(headers)))
    print(header_fmt)
    print("-" * sum(col_widths))

    # Rows
    for opt in options:
        row = (
            f"{opt['name']:<{col_widths[0]}}"
            f"{opt['type']:<{col_widths[1]}}"
            f"{opt['default']:<{col_widths[2]}}"
            f"{opt['current']:<{col_widths[3]}}"
            f"{opt['description']:<{col_widths[4]}}"
        )
        print(row)
    print("")


def handle_get_option(command: str) -> None:
    """Handle the 'get option' command."""
    option = command.split()[-1]
    value = sock.get_option_value(option)
    print(value)


def handle_set_option(command: str) -> None:
    """
    Handle the 'set option' command by parsing and updating Wayfire configuration.

    This function parses key-value pairs from the command string and transmits
    them to the compositor. It supports multiple options in a single call.

    Args:
        command: The raw command string (e.g., 'set option core/vwidth=4').
    """
    parts: list[str] = command.split()[2:]
    payload: dict[str, str] = {}

    for part in parts:
        if "=" not in part:
            print(f"Error: Invalid format for option '{part}'. Expected key=value.")
            continue

        key, value = part.split("=", 1)
        payload[key] = value

    if not payload:
        return

    try:
        sock.set_option_values(payload)
        for option, val in payload.items():
            print(f"Option {option} set to {val}")
    except Exception as e:
        print(f"Error: Failed to set options via IPC: {e}")


def handle_plugin_action(command: str, action: str) -> None:
    """Handle plugin-related actions (enable, disable, status)."""
    plugin_name = command.split()[-1]
    try:
        if action == "enable":
            enable_plugin(plugin_name)
        elif action == "disable":
            disable_plugin(plugin_name)
        elif action == "status":
            status_plugin(plugin_name)
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


def handle_list_config(command: str) -> None:
    """
    Handle the 'list config' command.

    Queries the live Wayfire configuration state.
    """
    try:
        response = sock.list_config_options()
        if response.get("result") != "ok":
            print("Error: Compositor communication failed.")
            return

        all_config = response.get("options", {})
        parts = command.split()

        if len(parts) > 2:
            query = parts[2].lower()
            filtered_config = {}

            for section, options in all_config.items():
                # Check if the query is in the section name
                section_match = query in section.lower()

                # Check if the query is in any of the keys (only if options is not None)
                key_match = False
                if options is not None:
                    key_match = any(query in opt.lower() for opt in options.keys())

                if section_match or key_match:
                    filtered_config[section] = options

            all_config = filtered_config

        if not all_config:
            print(f"No config matches found for: {parts[2]}")
            return

        print(json.dumps(all_config, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"Error: {e}")


def handle_move_view_to_workspace(command: str) -> None:
    """
    Handle the 'move view to workspace' command.

    Relocates a specific view to the target workspace coordinates.
    Usage: wfctl move view to workspace {view_id} {x} {y}
    """
    try:
        parts = command.split()
        if len(parts) < 6:
            print(
                "Error: Missing arguments. Usage: wfctl move view to workspace {id} {x} {y}"
            )
            return

        view_id = int(parts[4])
        ws_x = int(parts[5])
        ws_y = int(parts[6])

        result = sock.send_view_to_workspace(view_id, ws_x, ws_y)

        if result.get("result") == "ok":
            print(f"View {view_id} sent to workspace ({ws_x}, {ws_y})")
        else:
            print(f"Compositor error: {result}")

    except ValueError:
        print("Error: View ID and workspace coordinates must be integers.")
    except Exception as e:
        print(f"Error: {e}")


def handle_list_wsets() -> None:
    """Handle the 'list wsets' command."""
    s = sock.list_wsets()
    print(json.dumps(s, indent=4))


def handle_create_output(command: str) -> None:
    """Handle 'create output {width} {height}'."""
    try:
        parts = command.split()
        width, height = int(parts[2]), int(parts[3])
        result = sock.create_headless_output(width, height)
        print(f"Created headless output: {result}")
    except (IndexError, ValueError):
        print("Error: Usage: create output {width} {height}")


def handle_destroy_output(command: str) -> None:
    """
    Handle the 'destroy output {output_name}' command.

    Validates the existence of the specified output via IPC before
    attempting to destroy the headless instance.

    Args:
        command: The raw command string containing the target output name.

    Returns:
        None
    """
    try:
        parts: list[str] = command.split()
        if len(parts) < 3:
            print("Error: Usage: destroy output {output_name}")
            return

        output_name: str = parts[2]

        outputs: list[dict] = sock.list_outputs()
        exists: bool = any(output.get("name") == output_name for output in outputs)

        if not exists:
            print(f"Error: No output '{output_name}' found, skipping...")
            return

        result: dict = sock.destroy_headless_output(output_name)

        if result.get("result") == "ok":
            print(f"Successfully destroyed headless output: {output_name}")
        else:
            print(
                f"Compositor failed to destroy output: {result.get('error', 'Unknown error')}"
            )

    except Exception as e:
        print(f"An unexpected error occurred: {e}")


def handle_register_binding(command: str) -> None:
    """
    Handle 'register binding {key_combo} {shell_command}'.
    Example: wfctl register binding <super>KEY_T kitty
    """
    try:
        parts = command.split()
        binding = parts[2]
        cmd = " ".join(parts[3:])
        result = sock.register_binding(binding, command=cmd)
        print(f"Binding registered: {result}")
    except IndexError:
        print("Error: Usage: register binding {key} {command}")


def audit_plugins_abi(search_paths: list[str] | None = None) -> dict:
    """
    Audits Wayfire plugins for ABI compatibility across multiple paths.

    Checks paths provided in arguments, the WAYFIRE_PLUGIN_PATH env variable,
    and the system default /usr/lib/wayfire.
    """
    if "wayfire/get-plugin-abi-version" not in sock.list_methods():
        print("""Command not enabled, install/enable ipc-extra plugin: 
                 wfctl install plugin https://github.com/killown/wayfire-plugins ipc-extra""")
        sys.exit()

    # Resolve all candidate paths
    resolved_paths = []

    # Add paths from function arguments
    if search_paths:
        resolved_paths.extend(search_paths)

    # Add paths from Environment Variable
    env_path = os.getenv("WAYFIRE_PLUGIN_PATH")
    if env_path:
        resolved_paths.extend(env_path.split(":"))

    # Add default system path
    resolved_paths.append("/usr/lib/wayfire")

    # Filter for unique, existing directories
    final_paths = []
    for p in resolved_paths:
        p = os.path.abspath(os.path.expanduser(p))
        if os.path.isdir(p) and p not in final_paths:
            final_paths.append(p)

    report = {"compatible": [], "outdated": [], "failed": []}

    for current_path in final_paths:
        plugin_files = [f for f in os.listdir(current_path) if f.endswith(".so")]
        if not plugin_files:
            continue

        print(f"Auditing {len(plugin_files)} binaries in {current_path}...")

        for filename in plugin_files:
            full_path = os.path.join(current_path, filename)
            try:
                res = sock.send_json(
                    {
                        "method": "wayfire/get-plugin-abi-version",
                        "data": {"path": full_path},
                    }
                )

                plugin_data = {
                    "name": filename,
                    "path": current_path,
                    "plugin_abi": res.get("plugin_abi_version"),
                    "core_abi": res.get("wayfire_abi_version"),
                }

                if res.get("compatible"):
                    report["compatible"].append(plugin_data)
                else:
                    report["outdated"].append(plugin_data)

            except Exception as e:
                report["failed"].append({"name": filename, "error": str(e)})

    # Summary Display
    if report["outdated"]:
        print("\nOUTDATED PLUGINS (Rebuild required):")
        for p in report["outdated"]:
            print(
                f"  {p['name']} ({p['path']}): [Plugin: {p['plugin_abi']} | Core: {p['core_abi']}]"
            )

    if report["failed"]:
        print("\nERRORS (Invalid binaries or IPC issues):")
        for f in report["failed"]:
            print(f"  {f['name']}: {f['error']}")

    print(
        f"\nAudit complete: {len(report['compatible'])} compatible, {len(report['outdated'])} outdated."
    )
    return report


def handle_get_cursor_position() -> None:
    """
    Handle the 'get cursor position' command.
    Outputs the absolute X and Y coordinates of the mouse cursor.
    """
    try:
        pos = sock.get_cursor_position()
        if pos and len(pos) == 2:
            print(f"X: {pos[0]}, Y: {pos[1]}")
        else:
            print("Error: Could not retrieve cursor position from compositor.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


# Define command mapping to corresponding handler functions
command_map = {
    "audit plugins": audit_plugins_abi,
    "check abi": handle_check_abi,
    "close view": handle_close_view,
    "configure device": handle_configure_device,
    "create output": handle_create_output,
    "destroy output": handle_destroy_output,
    "disable plugin": lambda command: handle_plugin_action(command, "disable"),
    "enable plugin": lambda command: handle_plugin_action(command, "enable"),
    "fullscreen view": handle_fullscreen_view,
    "get cursor position": handle_get_cursor_position,
    "get focused output": handle_get_focused_output,
    "get focused view": handle_get_focused_view,
    "get focused workspace": handle_get_focused_workspace,
    "get keyboard": handle_get_keyboard,
    "get option": handle_get_option,
    "get view": handle_get_view,
    "install plugin": handle_install_plugin,
    "uninstall plugin": handle_uninstall_plugin,
    "list config": handle_list_config,
    "list inputs": handle_list_inputs,
    "list options": handle_list_options,
    "list outputs": handle_list_outputs,
    "list plugins": handle_list_plugins,
    "list views": handle_list_views,
    "list wsets": handle_list_wsets,
    "maximize view": handle_maximize_view,
    "minimize view": handle_minimize_view,
    "move view": handle_move_view,
    "move view to workspace": handle_move_view_to_workspace,
    "next workspace": handle_next_workspace,
    "register binding": handle_register_binding,
    "resize view": handle_resize_view,
    "search views": handle_search_views,
    "set keyboard": handle_set_keyboard,
    "set option": handle_set_option,
    "set view alpha": handle_set_view_alpha,
    "set workspace": handle_set_workspace,
    "status plugin": lambda command: handle_plugin_action(command, "status"),
    "update plugins": handle_update_plugins,
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
