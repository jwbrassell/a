"""
Plugin setup package initialization

Note: Plugin classes are imported lazily in PluginManager to avoid circular dependencies.
Each plugin setup module should be independent and only import what it needs when it needs it.
"""

__all__ = []  # Plugin classes are imported directly by PluginManager
