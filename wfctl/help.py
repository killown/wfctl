import argparse

def usage():
    parser = argparse.ArgumentParser(description="A command-line tool for interacting with Wayfire.")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Define all commands and their descriptions
    subparsers.add_parser("list views", help="List all views currently available.")
    subparsers.add_parser("list outputs", help="List all outputs connected to the system.")
    
    switch_workspace_parser = subparsers.add_parser("set workspace", help="Switch to a specific workspace.")
    switch_workspace_parser.add_argument("workspace_number", type=int, help="The workspace number to switch to.")
    
    subparsers.add_parser("get focused output", help="Get the currently focused output.")
    subparsers.add_parser("get focused view", help="Get the currently focused view.")
    subparsers.add_parser("get focused workspace", help="Get the currently focused workspace.")
    subparsers.add_parser("next workspace", help="Switch to the next workspace.")
    subparsers.add_parser("fullscreen view", help="Set fullscreen the view from the given id.")
    
    get_view_info_parser = subparsers.add_parser("get view info", help="Get information about a specific view using a given {view_id}.")
    get_view_info_parser.add_argument("view_id", type=int, help="The ID of the view to get information about.")
    
    resize_view_parser = subparsers.add_parser("resize view", help="Resize a specific view, wfctl resize view {view_id} width height.")
    resize_view_parser.add_argument("width", type=int, help="The new width of the view.")
    resize_view_parser.add_argument("height", type=int, help="The new height of the view.")
    
    move_view_parser = subparsers.add_parser("move view", help="Move a specific view, wfctl move view {view_id} x-coordinate y-coordinate.")
    move_view_parser.add_argument("view_id", type=int, help="The ID of the view to move.")
    move_view_parser.add_argument("x", type=int, help="The new x-coordinate of the view.")
    move_view_parser.add_argument("y", type=int, help="The new y-coordinate of the view.")
    
    close_view_parser = subparsers.add_parser("close view", help="Close a view using a given {view_id}.")
    close_view_parser.add_argument("view_id", type=int, help="The ID of the view to close.")

    minimize_view_parser = subparsers.add_parser("minimize view", help="minimize a view, wfctl minimize view {view_id} {true/false}.")
    minimize_view_parser.add_argument("view_id", type=int, help="The ID of the view to minimize.")
    minimize_view_parser.add_argument("bool", type=int, help="if minimize then true except use false")

    maximize_parser = subparsers.add_parser("maximize", help="Maximize a view from a given id.")
    maximize_parser.add_argument("view_id", type=int, help="The ID of the view to maximize or restore.")

    set_view_alpha_parser = subparsers.add_parser("set view alpha", help="Set view transparency, wfctl set view alpha {view_id} {0.4}.")
    set_view_alpha_parser.add_argument("view_id", type=int, help="The ID of the view to set alpha.")
    set_view_alpha_parser.add_argument("alpha", type=float, help="Float number...")

    subparsers.add_parser("-m", help="watch wayfire IPC events")

    subparsers.add_parser("list inputs", help="Lists all input devices currently available in the Wayfire environment")
    
    subparsers.add_parser("configure device", help="Configure a device input from a give ID, wfctl configure device {device_id} {enable/disable}")
    
    subparsers.add_parser("get option", help="Get wayfire config value from a given option, wfctl get option section/option")
    
    subparsers.add_parser("set option", help="Set wayfire config value from the given options, wfctl set options section_1/option_1:value_1 section_2/option_2:value_2")
    
    subparsers.add_parser("get keyboard", help="Retrieve the current keyboard layout, variant, model and options.")
    
    subparsers.add_parser("set keyboard", help="Set the keyboard layout, variant, model and options.")
    
    subparsers.add_parser("enable plugin", help="Enable a plugin from a given name.")
    subparsers.add_parser("disable plugin", help="Disable a plugin from a given name.")

    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()



