# wfctl

wayfire command line tool

    list views          List all views currently available.
    list outputs        List all outputs connected to the system.
    switch workspace    Switch to a specific workspace.
    get focused output  Get the currently focused output.
    get focused view    Get the currently focused view.
    get focused workspace
                        Get the currently focused workspace.
    next workspace      Switch to the next workspace.
    fullscreen view     Set a view fullscreen from a given id.
    get view info       Get information about a specific view using a given {view_id}.
    resize view         Resize a specific view, wfctl resize view {view_id} width height.
    move view           Move a specific view, wfctl move view {view_id} x-coordinate y-coordinate.
    close view          Close a view using a given {view_id}.
    minimize view       minimize a view, wfctl minimize view {view_id} {true/false}.
    maximize            Maximize or restore a view.
    set view alpha      Set view transparency, wfctl set view alpha {view_id} {0.4}.
