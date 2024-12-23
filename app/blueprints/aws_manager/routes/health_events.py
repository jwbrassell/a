from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration, AWSHealthEvent
from ..utils.websocket_service import HealthEventWebSocket
from app.extensions import socketio
from app.utils.enhanced_rbac import requires_permission
from ..utils import get_aws_manager

# Initialize WebSocket service
health_websocket = HealthEventWebSocket(socketio)

@aws_manager.route('/configurations/<int:config_id>/health')
@requires_permission('aws_access', 'read')
def list_health_events(config_id):
    """List AWS Health events"""
    config = AWSConfiguration.query.get_or_404(config_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON
        aws = get_aws_manager(config_id)
        try:
            events = aws.get_health_events(config_id)
            return jsonify(events)
        except Exception as e:
            current_app.logger.error(f"Failed to get health events: {str(e)}")
            abort(500, description=str(e))
    else:
        # Regular request - return HTML
        events = AWSHealthEvent.query.filter_by(aws_config_id=config_id).order_by(
            AWSHealthEvent.start_time.desc()
        ).all()
        return render_template('aws/health_events.html',
                             config_id=config_id,
                             events=events,
                             active_page='health')

@aws_manager.route('/configurations/<int:config_id>/health/refresh', methods=['POST'])
@requires_permission('aws_access', 'read')
def refresh_health_events(config_id):
    """Refresh AWS Health events"""
    aws = get_aws_manager(config_id)
    try:
        events = aws.get_health_events(config_id)
        
        # Broadcast new events to connected clients
        for event in events:
            health_websocket.broadcast_health_event(config_id, event)
        
        return jsonify({
            'message': 'Successfully refreshed health events',
            'event_count': len(events)
        })
    except Exception as e:
        current_app.logger.error(f"Failed to refresh health events: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/health/events/<event_arn>')
@requires_permission('aws_access', 'read')
def get_health_event(config_id, event_arn):
    """Get details for a specific health event"""
    event = AWSHealthEvent.query.filter_by(
        aws_config_id=config_id,
        event_arn=event_arn
    ).first_or_404()
    
    return jsonify({
        'event_arn': event.event_arn,
        'service': event.service,
        'event_type_code': event.event_type_code,
        'event_type_category': event.event_type_category,
        'region': event.region,
        'start_time': event.start_time.isoformat() if event.start_time else None,
        'end_time': event.end_time.isoformat() if event.end_time else None,
        'status': event.status,
        'affected_resources': event.affected_resources,
        'description': event.description
    })
