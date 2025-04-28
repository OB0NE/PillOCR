import os
import sys

def get_absolute_path(relative_path):
    """Get the absolute path of the resource file"""
    try:
        # Packaged environment
        base_path = sys._MEIPASS
        # Adapt to _internal directory for PyInstaller 6.0 and above
        internal_path = os.path.join(base_path, '_internal')
        if os.path.exists(os.path.join(internal_path, relative_path)):
            base_path = internal_path
    except Exception:
        # Development environment
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)