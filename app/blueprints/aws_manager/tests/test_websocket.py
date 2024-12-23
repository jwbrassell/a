"""
WebSocket Service Tests
--------------------
Tests for WebSocket service and real-time health event notifications.
"""

import pytest
import json
import asyncio
from unittest.mock import patch, MagicMock
from ..utils.websocket_service import HealthEventWebSocket

@pytest.fixture
def websocket_service():
    """Create a WebSocket service instance"""
    return HealthEventWebSocket()

@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection"""
    ws = MagicMock()
    ws.send = MagicMock()
    ws.close = MagicMock()
    return ws

@pytest.fixture
def mock_event():
    """Create a mock health event"""
    return {
        'event_arn': 'arn:aws:health:us-east-1::event/test',
        'service': 'EC2',
        'event_type_code': 'AWS_EC2_INSTANCE_ISSUE',
        'event_type_category': 'issue',
        'region': 'us-east-1',
        'status': 'open',
        'start_time': '2023-01-01T00:00:00Z',
        'affected_resources': ['i-1234567890abcdef0'],
        'description': 'Test event description'
    }

class TestHealthEventWebSocket:
    """Test WebSocket service"""
    
    def test_initialization(self, websocket_service):
        """Test WebSocket service initialization"""
        assert websocket_service.connections == set()
        assert websocket_service.event_history == []
        
    def test_add_connection(self, websocket_service, mock_websocket):
        """Test adding WebSocket connection"""
        websocket_service.add_connection(mock_websocket)
        assert mock_websocket in websocket_service.connections
        
    def test_remove_connection(self, websocket_service, mock_websocket):
        """Test removing WebSocket connection"""
        websocket_service.add_connection(mock_websocket)
        websocket_service.remove_connection(mock_websocket)
        assert mock_websocket not in websocket_service.connections
        
    def test_broadcast_event(self, websocket_service, mock_websocket, mock_event):
        """Test broadcasting event to connections"""
        websocket_service.add_connection(mock_websocket)
        websocket_service.broadcast_event(mock_event)
        
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data['event_type_code'] == 'AWS_EC2_INSTANCE_ISSUE'
        
    def test_broadcast_event_no_connections(self, websocket_service, mock_event):
        """Test broadcasting event with no connections"""
        # Should not raise any exceptions
        websocket_service.broadcast_event(mock_event)
        assert len(websocket_service.event_history) == 1
        
    def test_event_history(self, websocket_service, mock_event):
        """Test event history management"""
        # Add multiple events
        for i in range(15):  # More than max history
            event = mock_event.copy()
            event['event_arn'] = f"{event['event_arn']}-{i}"
            websocket_service.broadcast_event(event)
            
        # Check history limit
        assert len(websocket_service.event_history) == 10  # Default max history
        
        # Check order (most recent first)
        assert websocket_service.event_history[0]['event_arn'].endswith('-14')
        
    def test_send_event_history(self, websocket_service, mock_websocket, mock_event):
        """Test sending event history to new connection"""
        # Add some events to history
        websocket_service.broadcast_event(mock_event)
        
        # Add connection and check history sent
        websocket_service.add_connection(mock_websocket)
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert isinstance(sent_data, list)
        assert len(sent_data) == 1
        
    def test_handle_connection_error(self, websocket_service, mock_websocket, mock_event):
        """Test handling connection errors during broadcast"""
        mock_websocket.send.side_effect = Exception("Connection error")
        websocket_service.add_connection(mock_websocket)
        
        # Should remove problematic connection
        websocket_service.broadcast_event(mock_event)
        assert mock_websocket not in websocket_service.connections

@pytest.mark.asyncio
class TestAsyncWebSocket:
    """Test asynchronous WebSocket operations"""
    
    async def test_async_broadcast(self, websocket_service, mock_websocket, mock_event):
        """Test asynchronous event broadcasting"""
        websocket_service.add_connection(mock_websocket)
        
        # Simulate multiple concurrent broadcasts
        await asyncio.gather(
            websocket_service.async_broadcast(mock_event),
            websocket_service.async_broadcast(mock_event)
        )
        
        assert mock_websocket.send.call_count == 2
        
    async def test_connection_lifecycle(self, websocket_service, mock_websocket):
        """Test complete connection lifecycle"""
        # Add connection
        await websocket_service.async_add_connection(mock_websocket)
        assert mock_websocket in websocket_service.connections
        
        # Send some events
        mock_event = {
            'event_arn': 'test-arn',
            'message': 'test message'
        }
        await websocket_service.async_broadcast(mock_event)
        assert mock_websocket.send.called
        
        # Remove connection
        await websocket_service.async_remove_connection(mock_websocket)
        assert mock_websocket not in websocket_service.connections
        
    async def test_concurrent_connections(self, websocket_service):
        """Test handling multiple concurrent connections"""
        connections = [MagicMock() for _ in range(5)]
        
        # Add connections concurrently
        await asyncio.gather(
            *[websocket_service.async_add_connection(ws) for ws in connections]
        )
        
        assert len(websocket_service.connections) == 5
        
        # Broadcast to all connections
        mock_event = {'message': 'test'}
        await websocket_service.async_broadcast(mock_event)
        
        for ws in connections:
            assert ws.send.called

@pytest.mark.integration
class TestWebSocketIntegration:
    """Integration tests for WebSocket service"""
    
    def test_full_event_flow(self, websocket_service, mock_websocket, mock_event):
        """Test complete event flow through WebSocket"""
        # Setup connection
        websocket_service.add_connection(mock_websocket)
        
        # Broadcast event
        websocket_service.broadcast_event(mock_event)
        
        # Verify event received
        mock_websocket.send.assert_called_once()
        sent_data = json.loads(mock_websocket.send.call_args[0][0])
        assert sent_data['event_arn'] == mock_event['event_arn']
        
        # Verify event in history
        assert len(websocket_service.event_history) == 1
        assert websocket_service.event_history[0]['event_arn'] == mock_event['event_arn']
        
        # Add new connection
        new_ws = MagicMock()
        websocket_service.add_connection(new_ws)
        
        # Verify history sent to new connection
        new_ws.send.assert_called_once()
        history_data = json.loads(new_ws.send.call_args[0][0])
        assert isinstance(history_data, list)
        assert len(history_data) == 1
        
        # Close connections
        websocket_service.remove_connection(mock_websocket)
        websocket_service.remove_connection(new_ws)
        assert len(websocket_service.connections) == 0
