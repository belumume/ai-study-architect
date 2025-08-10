"""
Path setup module - MUST be imported before any other app imports.
This ensures Python can find all modules on Render deployment.
"""
import sys
import os

# Get the backend directory (parent of app directory)
_current_file = os.path.abspath(__file__)
_app_dir = os.path.dirname(_current_file)
_backend_dir = os.path.dirname(_app_dir)

# Add backend directory to Python path
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)
    print(f"[PATH_SETUP] Added to sys.path: {_backend_dir}")

# Also add Render's specific path if we're on Render
render_path = "/opt/render/project/src/project/backend"
if os.path.exists(render_path) and render_path not in sys.path:
    sys.path.insert(0, render_path)
    print(f"[PATH_SETUP] Added Render path: {render_path}")

# Verify we can import app
try:
    import app
    print(f"[PATH_SETUP] [OK] app module found at: {app.__file__}")
except ImportError as e:
    print(f"[PATH_SETUP] [ERROR] Cannot import app: {e}")
    # Try to diagnose
    print(f"[PATH_SETUP] Current directory: {os.getcwd()}")
    print(f"[PATH_SETUP] Directory contents: {os.listdir('.')}")
    print(f"[PATH_SETUP] sys.path: {sys.path[:5]}")