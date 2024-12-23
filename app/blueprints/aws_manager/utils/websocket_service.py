import json
from flask import current_app
from flask_socketio import SocketIO, emit, join_room, leave_room
from typing import Dict, Set, Optional
from datetime import datetime

class HealthEventWebSocket:
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.user_preferences: Dict[str, Dict] = {}  # user_id -> preferences
        self.user_rooms: Dict[str, Set[str]] = {}  # user_id -> set of room names
        
        # Register event handlers
        @socketio.on('connect', namespace='/health')
        def handle_connect():
            current_app.logger.info('Client connected to health events websocket')
        
        @socketio.on('disconnect', namespace='/health')
        def handle_disconnect():
            user_id = self._get_user_id()
            if user_id:
                self._cleanup_user(user_id)
                current_app.logger.info(f'User {user_id} disconnected from health events')
        
        @socketio.on('join', namespace='/health')
        def handle_join(data):
            user_id = self._get_user_id()
            if not user_id:
                return
            
            config_id = data.get('config_id')
            if not config_id:
                return
            
            room = f'health_events_{config_id}'
            join_room(room)
            
            if user_id not in self.user_rooms:
                self.user_rooms[user_id] = set()
            self.user_rooms[user_id].add(room)
            
            current_app.logger.info(f'User {user_id} joined room {room}')
        
        @socketio.on('leave', namespace='/health')
        def handle_leave(data):
            user_id = self._get_user_id()
            if not user_id:
                return
            
            config_id = data.get('config_id')
            if not config_id:
                return
            
            room = f'health_events_{config_id}'
            leave_room(room)
            
            if user_id in self.user_rooms:
                self.user_rooms[user_id].discard(room)
            
            current_app.logger.info(f'User {user_id} left room {room}')
        
        @socketio.on('set_preferences', namespace='/health')
        def handle_preferences(data):
            user_id = self._get_user_id()
            if not user_id:
                return
            
            preferences = {
                'notify_critical': data.get('notify_critical', True),
                'notify_warning': data.get('notify_warning', True),
                'notify_info': data.get('notify_info', False),
                'event_types': data.get('event_types', []),
                'services': data.get('services', [])
            }
            
            self.user_preferences[user_id] = preferences
            current_app.logger.info(f'Updated preferences for user {user_id}')
            
            # Acknowledge the update
            emit('preferences_updated', preferences)
    
    def broadcast_health_event(self, config_id: int, event_data: Dict):
        """Broadcast a health event to all connected clients in the config room"""
        room = f'health_events_{config_id}'
        
        # Add timestamp for client-side ordering
        event_data['broadcast_time'] = datetime.utcnow().isoformat()
        
        self.socketio.emit('health_event', event_data, room=room, namespace='/health')
        current_app.logger.info(f'Broadcasted health event to room {room}')
    
    def notify_user(self, user_id: str, event_data: Dict) -> bool:
        """
        Check if a user should be notified of an event based on their preferences
        Returns True if notification was sent, False otherwise
        """
        preferences = self.user_preferences.get(user_id)
        if not preferences:
            return False
        
        # Check event severity preferences
        severity = self._get_event_severity(event_data)
        if severity == 'critical' and not preferences['notify_critical']:
            return False
        if severity == 'warning' and not preferences['notify_warning']:
            return False
        if severity == 'info' and not preferences['notify_info']:
            return False
        
        # Check event type preferences
        if preferences['event_types']:
            if event_data['event_type_category'] not in preferences['event_types']:
                return False
        
        # Check service preferences
        if preferences['services']:
            if event_data['service'] not in preferences['services']:
                return False
        
        # Send notification to specific user
        self.socketio.emit(
            'health_notification',
            event_data,
            room=user_id,
            namespace='/health'
        )
        current_app.logger.info(f'Sent health notification to user {user_id}')
        return True
    
    def _get_user_id(self) -> Optional[str]:
        """Get the current user's ID from the session"""
        # This should be implemented based on your authentication system
        return None  # Placeholder
    
    def _cleanup_user(self, user_id: str):
        """Clean up user data when they disconnect"""
        # Remove from all rooms
        if user_id in self.user_rooms:
            for room in self.user_rooms[user_id]:
                leave_room(room)
            del self.user_rooms[user_id]
        
        # Clear preferences
        if user_id in self.user_preferences:
            del self.user_preferences[user_id]
    
    def _get_event_severity(self, event_data: Dict) -> str:
        """Determine event severity based on status and category"""
        status = event_data.get('status', '').lower()
        category = event_data.get('event_type_category', '').lower()
        
        if status == 'open' or 'error' in category or 'issue' in category:
            return 'critical'
        elif status == 'upcoming' or 'scheduled' in category:
            return 'warning'
        else:
            return 'info'
