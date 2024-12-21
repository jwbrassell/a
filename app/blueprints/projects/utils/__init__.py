"""Utility functions for the projects plugin."""

# Import functions lazily to avoid circular imports
def init_project_settings(*args, **kwargs):
    from .init_project_settings import init_project_settings as _init
    return _init(*args, **kwargs)

def register_project_routes(*args, **kwargs):
    from .register_routes import register_project_routes as _register
    return _register(*args, **kwargs)

__all__ = ['init_project_settings', 'register_project_routes']
