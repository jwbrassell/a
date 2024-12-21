import os
from flask import current_app
from typing import Dict, List

class ImageRegistry:
    """Registry for managing application images like avatars and loaders."""
    
    _avatars: Dict[str, str] = {}
    _loaders: Dict[str, str] = {}
    
    @classmethod
    def init_app(cls, app):
        """Initialize the image registry with the application context."""
        with app.app_context():
            # Scan avatar images
            avatar_path = os.path.join(app.static_folder, 'images', 'avatars')
            if os.path.exists(avatar_path):
                for filename in os.listdir(avatar_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        name = os.path.splitext(filename)[0]
                        cls._avatars[name] = f'images/avatars/{filename}'
            
            # Scan loader images
            loader_path = os.path.join(app.static_folder, 'images', 'loaders')
            if os.path.exists(loader_path):
                for filename in os.listdir(loader_path):
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        name = os.path.splitext(filename)[0]
                        cls._loaders[name] = f'images/loaders/{filename}'
            
            # Register template context processors
            app.context_processor(lambda: {
                'get_avatar': cls.get_avatar,
                'get_loader': cls.get_loader,
                'list_avatars': cls.list_avatars,
                'list_loaders': cls.list_loaders
            })
    
    @classmethod
    def get_avatar(cls, name: str) -> str:
        """Get the URL for an avatar image by name."""
        if name in cls._avatars:
            return cls._avatars[name]
        # Return a default avatar if the requested one doesn't exist
        return cls._avatars.get('user_1', 'images/avatars/user_1.jpg')
    
    @classmethod
    def get_loader(cls, name: str) -> str:
        """Get the URL for a loader image by name."""
        if name in cls._loaders:
            return cls._loaders[name]
        # Return first available loader or None
        return next(iter(cls._loaders.values()), None)
    
    @classmethod
    def list_avatars(cls) -> List[Dict[str, str]]:
        """Get a list of all available avatars."""
        return [{'name': name, 'url': url} for name, url in cls._avatars.items()]
    
    @classmethod
    def list_loaders(cls) -> List[Dict[str, str]]:
        """Get a list of all available loaders."""
        return [{'name': name, 'url': url} for name, url in cls._loaders.items()]
    
    @classmethod
    def refresh(cls):
        """Refresh the registry by rescanning the image directories."""
        cls._avatars.clear()
        cls._loaders.clear()
        cls.init_app(current_app._get_current_object())
