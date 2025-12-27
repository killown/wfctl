def usage() -> None:
    """
    Generate and display the help documentation for wfctl.
    Commands are sorted alphabetically for improved UX.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description="wfctl: An advanced lifecycle and state management utility for the Wayfire Compositor."
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # --- Sorted Command Definitions ---

    audit_plugins_parser = subparsers.add_parser(
        "audit plugins", help="Check for outdated plugins binary compatibility (ABI)."
    )
    audit_plugins_parser.add_argument(
        "path", nargs="?", help="Optional directory to scan."
    )

    check_abi_parser = subparsers.add_parser(
        "check abi", help="Check plugin binary compatibility (ABI)."
    )
    check_abi_parser.add_argument("path", help="Path to the .so plugin file.")

    close_view_parser = subparsers.add_parser("close view", help="Close a view by ID.")
    close_view_parser.add_argument("view_id", type=int)

    conf_dev_parser = subparsers.add_parser(
        "configure device", help="Enable/Disable device."
    )
    conf_dev_parser.add_argument("device_id", type=str)
    conf_dev_parser.add_argument("status", choices=["enable", "disable"])

    subparsers.add_parser("create output", help="Create headless display.")

    dest_out_parser = subparsers.add_parser(
        "destroy output", help="Remove a virtual headless display."
    )
    dest_out_parser.add_argument("output_name", help="Name of the headless output.")

    subparsers.add_parser("disable plugin", help="Disable a plugin from a given name.")
    subparsers.add_parser("enable plugin", help="Enable a plugin from a given name.")

    fullscreen_view_parser = subparsers.add_parser(
        "fullscreen view", help="Set fullscreen state."
    )
    fullscreen_view_parser.add_argument("view_id", type=int)
    fullscreen_view_parser.add_argument("state", choices=["true", "false"])

    subparsers.add_parser("get cursor position", help="Get current mouse coordinates.")
    subparsers.add_parser("get focused output", help="Details of the active output.")
    subparsers.add_parser("get focused view", help="Details of the active view.")
    subparsers.add_parser(
        "get focused workspace", help="Index of the active workspace."
    )
    subparsers.add_parser("get keyboard", help="List layouts and active index.")

    get_opt_parser = subparsers.add_parser(
        "get option", help="Get section/option value."
    )
    get_opt_parser.add_argument("option", help="Format: section/option")

    get_view_parser = subparsers.add_parser(
        "get view", help="Get detailed info for a view."
    )
    get_view_parser.add_argument("view_id", type=int)

    inst_plugin_parser = subparsers.add_parser(
        "install plugin", help="Install from Git URL."
    )
    inst_plugin_parser.add_argument("repo_url")
    inst_plugin_parser.add_argument("plugin_name", nargs="?")

    list_config_parser = subparsers.add_parser(
        "list config", help="List live configuration options."
    )
    list_config_parser.add_argument("filter", nargs="?", help="Substring filter.")

    subparsers.add_parser("list inputs", help="List all connected input devices.")
    subparsers.add_parser("list outputs", help="List all physical and virtual outputs.")
    subparsers.add_parser(
        "list plugins", help="Show all installed plugins and their status."
    )
    subparsers.add_parser("list views", help="List all views currently available.")
    subparsers.add_parser("list wsets", help="List all workspace sets.")

    subparsers.add_parser("-m", help="Monitor real-time IPC events.")

    maximize_view_parser = subparsers.add_parser(
        "maximize view", help="Maximize a view."
    )
    maximize_view_parser.add_argument("view_id", type=int)

    minimize_view_parser = subparsers.add_parser(
        "minimize view", help="Minimize or restore a view."
    )
    minimize_view_parser.add_argument("view_id", type=int)
    minimize_view_parser.add_argument("state", choices=["true", "false"])

    move_view_parser = subparsers.add_parser(
        "move view", help="Move view to absolute coordinates."
    )
    move_view_parser.add_argument("view_id", type=int)
    move_view_parser.add_argument("x", type=int)
    move_view_parser.add_argument("y", type=int)

    mv_ws_parser = subparsers.add_parser(
        "move view to workspace", help="Send view to workspace."
    )
    mv_ws_parser.add_argument("view_id", type=int)
    mv_ws_parser.add_argument("x", type=int)
    mv_ws_parser.add_argument("y", type=int)

    subparsers.add_parser("next workspace", help="Cycle to the next workspace.")

    reg_bind_parser = subparsers.add_parser(
        "register binding", help="Map dynamic hotkey."
    )
    reg_bind_parser.add_argument("key")
    reg_bind_parser.add_argument("shell_cmd")

    resize_view_parser = subparsers.add_parser(
        "resize view", help="Change view dimensions."
    )
    resize_view_parser.add_argument("view_id", type=int)
    resize_view_parser.add_argument("width", type=int)
    resize_view_parser.add_argument("height", type=int)

    subparsers.add_parser("search views", help="Search windows by property/value.")

    set_kb_parser = subparsers.add_parser(
        "set keyboard", help="Switch layout by index."
    )
    set_kb_parser.add_argument("index", type=int)

    set_opt_parser = subparsers.add_parser(
        "set option", help="Set section/option value."
    )
    set_opt_parser.add_argument("pair", help="Format: section/option=value")

    set_alpha_parser = subparsers.add_parser("set view alpha", help="Set transparency.")
    set_alpha_parser.add_argument("view_id", type=int)
    set_alpha_parser.add_argument("alpha", type=float)

    set_ws_parser = subparsers.add_parser(
        "set workspace", help="Switch current workspace."
    )
    set_ws_parser.add_argument("index", type=int)

    status_plugin_parser = subparsers.add_parser(
        "status plugin", help="Check if plugin is active."
    )
    status_plugin_parser.add_argument("plugin_name")

    uninstall_plugin_parser = subparsers.add_parser(
        "uninstall plugin", help="Remove a plugin binary and its metadata."
    )
    uninstall_plugin_parser.add_argument(
        "plugin_name", help="Name of the plugin to uninstall."
    )

    subparsers.add_parser("update plugins", help="Batch update Git-installed plugins.")

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)

    try:
        parser.parse_known_args()
    except (argparse.ArgumentError, argparse.ArgumentTypeError):
        sys.exit(1)
