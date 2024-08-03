wfctl
=====

A command-line tool for interacting with Wayfire.

Installation
------------

To install wfctl, run:

.. code-block:: bash

    pip install wfctl

Usage
-----

To use wfctl, run:

.. code-block:: bash

    wfctl <command>


    list views            List all views currently available.
    list outputs          List all outputs connected to the system.
    switch workspace      Switch to a specific workspace.
    get focused output    Get the currently focused output.
    get focused view      Get the currently focused view.
    get focused workspace Get the currently focused workspace.
    next workspace        Switch to the next workspace.
    fullscreen view       Set a view fullscreen from a given id.
    get view info         Get information about a specific view using a given {view_id}.
    resize view           Resize a specific view, wfctl resize view {view_id} width height.
    move view             Move a specific view, wfctl move view {view_id} x-coordinate y-coordinate.
    close view            Close a view using a given {view_id}.
    minimize view         minimize a view, wfctl minimize view {view_id} {true/false}.
    maximize              Maximize a view from a given id.
    set view alpha        Set view transparency, wfctl set view alpha {view_id} {0.4}.
    list input            Lists all input devices currently available in the Wayfire environment
    configure device      Configure a device input from a give ID, wfctl configure device {device_id} {enable/disable}
    get option            Get wayfire config value from a given option, wfctl get option section/option
    set options           Set wayfire config value from the given options, wfctl set options section_1/option_1:value_1 section_2/option_2:value_2
    get keyboard          Retrieve the current keyboard layout, variant, model and options.
    set keyboard          Set the keyboard layout, variant, model and options.
    -m                    watch wayfire events

Contributing
------------

Contributions are welcome! Please open an issue or submit a pull request.

License
-------

This project is licensed under the MIT License.

