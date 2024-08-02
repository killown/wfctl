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

