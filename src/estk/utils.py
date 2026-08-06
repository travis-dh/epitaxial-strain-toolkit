"""utils.py: Shared helper functions and filesystem-safe naming utilities."""

def miller_label(hkl: tuple) -> str:
    """
    Converts a Miller index tuple to a string label.
    Uses 'n' for negative values (e.g., (1, -1, 0) -> '1n10').
    
    Args:
        hkl: A tuple of three integers (h, k, l).
        
    Returns:
        A string representing the Miller index.
    """
    label = ""
    for val in hkl:
        if val < 0:
            label += f"n{abs(val)}"
        else:
            label += str(val)
    return label

def strain_label(strain_pct: float) -> str:
    """
    Converts a strain percentage to a standard directory name.
    Uses 'n' for negative values (e.g., -4.0 -> 'strain_n4.0').
    
    Args:
        strain_pct: The strain as a percentage (e.g., -4.0, 0.5).
        
    Returns:
        A string formatted as 'strain_[n]X.X'.
    """
    # Using 'n' instead of '-' avoids potential issues on HPC clusters.
    if strain_pct < 0:
        return f"strain_n{abs(strain_pct):.1f}"
    else:
        return f"strain_{strain_pct:.1f}"