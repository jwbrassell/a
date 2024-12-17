"""Alert service for metric-based monitoring."""

from flask import current_app
from datetime import datetime, timedelta
import logging
from app.extensions import db
from app.models.metrics import MetricAlert, Metric
from app.utils.websocket_service import monitoring_ns
from app.utils.email_service import send_notification_email
import json
from typing import Dict, Any, List
from dataclasses import dataclass
from threading import Thread
import time

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class AlertCondition:
    """Represents an alert condition check result."""
    alert: MetricAlert
    current_value: float
    threshold: float
    triggered: bool
    duration_met: bool

class AlertService:
    """Service for managing and processing metric-based alerts."""
    
    def __init__(self, app=None):
        """Initialize alert service."""
        self.app = app
        self._alert_history = {}  # Track alert states
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask application."""
        self.app = app
        
        # Start alert checking in background
        if app.config.get('ALERT_CHECKING_ENABLED', True):
            self._start_alert_checking()
    
    def _start_alert_checking(self):
        """Start background alert checking."""
        def check_alerts_periodically():
            while True:
                try:
                    with self.app.app_context():
                        self.check_all_alerts()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Error checking alerts: {e}")
        
        thread = Thread(target=check_alerts_periodically, daemon=True)
        thread.start()
    
    def create_alert(self, name: str, metric_name: str, condition: str,
                    threshold: float, duration: int, tags: Dict[str, str] = None) -> MetricAlert:
        """Create a new metric alert."""
        try:
            alert = MetricAlert(
                name=name,
                metric_name=metric_name,
                condition=condition,
                threshold=threshold,
                duration=duration,
                tags=json.dumps(tags or {})
            )
            
            db.session.add(alert)
            db.session.commit()
            
            logger.info(f"Created alert: {alert}")
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {e}")
            db.session.rollback()
            raise
    
    def update_alert(self, alert_id: int, **kwargs) -> MetricAlert:
        """Update an existing alert."""
        try:
            alert = MetricAlert.query.get(alert_id)
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(alert, key):
                    if key == 'tags' and isinstance(value, dict):
                        value = json.dumps(value)
                    setattr(alert, key, value)
            
            db.session.commit()
            logger.info(f"Updated alert: {alert}")
            return alert
            
        except Exception as e:
            logger.error(f"Error updating alert: {e}")
            db.session.rollback()
            raise
    
    def delete_alert(self, alert_id: int) -> bool:
        """Delete an alert."""
        try:
            alert = MetricAlert.query.get(alert_id)
            if alert:
                db.session.delete(alert)
                db.session.commit()
                logger.info(f"Deleted alert: {alert}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting alert: {e}")
            db.session.rollback()
            raise
    
    def check_alert_condition(self, alert: MetricAlert) -> AlertCondition:
        """Check if an alert condition is met."""
        try:
            # Get recent metrics
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=alert.duration)
            
            metrics = Metric.query.filter_by(name=alert.metric_name)
            if alert.tags:
                tags = json.loads(alert.tags)
                for key, value in tags.items():
                    metrics = metrics.filter(Metric.tags[key].astext == value)
            
            metrics = metrics.filter(
                Metric.timestamp.between(start_time, end_time)
            ).order_by(Metric.timestamp.desc()).all()
            
            if not metrics:
                return AlertCondition(alert, 0, alert.threshold, False, False)
            
            # Calculate average value over duration
            total_value = sum(m.value for m in metrics)
            avg_value = total_value / len(metrics)
            
            # Check if condition is met
            triggered = alert.check_condition(avg_value)
            
            # Check if condition has been met for the entire duration
            duration_met = len(metrics) >= 2 and all(
                alert.check_condition(m.value) for m in metrics
            )
            
            return AlertCondition(
                alert=alert,
                current_value=avg_value,
                threshold=alert.threshold,
                triggered=triggered,
                duration_met=duration_met
            )
            
        except Exception as e:
            logger.error(f"Error checking alert condition: {e}")
            return AlertCondition(alert, 0, alert.threshold, False, False)
    
    def check_all_alerts(self):
        """Check all enabled alerts."""
        try:
            alerts = MetricAlert.query.filter_by(enabled=True).all()
            
            for alert in alerts:
                condition = self.check_alert_condition(alert)
                
                # Get previous state
                prev_state = self._alert_history.get(alert.id, {
                    'triggered': False,
                    'notified': False,
                    'last_check': None
                })
                
                # Check if alert should be triggered
                if condition.triggered and condition.duration_met:
                    if not prev_state['notified']:
                        # New alert trigger
                        self._send_alert_notification(alert, condition)
                        prev_state['notified'] = True
                else:
                    # Reset notification state when condition is no longer met
                    prev_state['notified'] = False
                
                # Update state
                prev_state['triggered'] = condition.triggered
                prev_state['last_check'] = datetime.utcnow()
                self._alert_history[alert.id] = prev_state
                
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
    
    def _send_alert_notification(self, alert: MetricAlert, condition: AlertCondition):
        """Send alert notification."""
        try:
            # Update alert last triggered time
            alert.last_triggered = datetime.utcnow()
            db.session.commit()
            
            # Prepare alert data
            alert_data = {
                'id': alert.id,
                'name': alert.name,
                'metric_name': alert.metric_name,
                'condition': alert.condition,
                'threshold': alert.threshold,
                'current_value': condition.current_value,
                'triggered_at': datetime.utcnow().isoformat(),
                'tags': json.loads(alert.tags) if isinstance(alert.tags, str) else alert.tags
            }
            
            # Emit via WebSocket for real-time updates
            monitoring_ns.emit_alert(alert_data)
            
            # Send email notification
            subject = f"System Alert: {alert.name}"
            body = f"""
System Alert Notification
------------------------

Alert Name: {alert.name}
Metric: {alert.metric_name}
Condition: {alert.condition} {alert.threshold}
Current Value: {condition.current_value:.2f}
Triggered At: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}

Additional Details:
{json.dumps(alert_data.get('tags', {}), indent=2)}

This is an automated message from the system monitoring service.
"""
            
            # Send to admin users (in development, this will be logged instead of sent)
            send_notification_email(subject, body, ['admin@localhost'])
            
            logger.info(f"Alert notification sent: {alert_data}")
            
        except Exception as e:
            logger.error(f"Error sending alert notification: {e}")
            db.session.rollback()

# Initialize alert service
alert_service = AlertService()
