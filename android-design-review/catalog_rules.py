"""Catalog eligibility for the Android portrait-screen review workflow."""
import math


def is_screen(entry):
    if entry.get('kind') == 'note':
        return False
    try:
        width, height = float(entry['width']), float(entry['height'])
    except (KeyError, TypeError, ValueError):
        return True  # Keep older imports whose dimensions are unknown.
    return (math.isfinite(width) and math.isfinite(height)
            and width >= 160 and height >= 300 and height / width >= 1.35)
