# Monitoring & Alerts Implementation Improvements

## 1. Metric Storage Implementation

### Current Status
- Basic metric alert system
- Real-time WebSocket notifications
- Email notifications
- Alert condition checking

### Improvements

#### A. Enhanced Metric Storage System

1. Metric Data Structure
```python
class MetricStorage:
    """Enhanced metric storage with retention management."""
    
    def __init__(self, retention_days=7):
        self.retention_days = retention_days
        self.cleanup_threshold = 1000  # Records before cleanup
    
    def store_metric(self, name: str, value: float, tags: dict = None):
        """Store a new metric with cleanup check."""
        try:
            metric = Metric(
                name=name,
                value=value,
                tags=json.dumps(tags or {}),
                timestamp=datetime.utcnow()
            )
            
            db.session.add(metric)
            
            # Check if cleanup needed
            if self._needs_cleanup():
                self._cleanup_old_metrics()
            
            db.session.commit()
            return metric
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error storing metric: {e}")
            raise
    
    def _needs_cleanup(self) -> bool:
        """Check if metric cleanup is needed."""
        count = Metric.query.count()
        return count > self.cleanup_threshold
    
    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        Metric.query.filter(Metric.timestamp < cutoff).delete()
```

2. Basic Trend Analysis
```python
class MetricAnalyzer:
    """Analyze metric trends and patterns."""
    
    @staticmethod
    def calculate_trend(metric_name: str, hours: int = 24) -> dict:
        """Calculate trend for a metric over specified hours."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = Metric.query.filter_by(name=metric_name)\
            .filter(Metric.timestamp.between(start_time, end_time))\
            .order_by(Metric.timestamp.asc())\
            .all()
        
        if not metrics:
            return {
                'trend': 'no_data',
                'avg': 0,
                'min': 0,
                'max': 0
            }
        
        values = [m.value for m in metrics]
        
        return {
            'trend': 'up' if values[-1] > values[0] else 'down',
            'avg': sum(values) / len(values),
            'min': min(values),
            'max': max(values)
        }
```

#### B. System Health Alerts Configuration

1. Default Alert Templates
```python
SYSTEM_HEALTH_ALERTS = {
    'cpu_usage': {
        'name': 'High CPU Usage',
        'metric_name': 'system.cpu.usage',
        'condition': '>',
        'threshold': 80.0,  # 80% CPU usage
        'duration': 300,    # 5 minutes
        'severity': 'warning'
    },
    'memory_usage': {
        'name': 'High Memory Usage',
        'metric_name': 'system.memory.usage',
        'condition': '>',
        'threshold': 90.0,  # 90% memory usage
        'duration': 300,    # 5 minutes
        'severity': 'warning'
    },
    'disk_space': {
        'name': 'Low Disk Space',
        'metric_name': 'system.disk.usage',
        'condition': '>',
        'threshold': 85.0,  # 85% disk usage
        'duration': 3600,   # 1 hour
        'severity': 'warning'
    }
}
```

2. Alert Configuration Manager
```python
class AlertConfigManager:
    """Manage system health alert configurations."""
    
    @staticmethod
    def setup_default_alerts():
        """Set up default system health alerts."""
        for alert_type, config in SYSTEM_HEALTH_ALERTS.items():
            existing = MetricAlert.query.filter_by(
                metric_name=config['metric_name']
            ).first()
            
            if not existing:
                alert = MetricAlert(
                    name=config['name'],
                    metric_name=config['metric_name'],
                    condition=config['condition'],
                    threshold=config['threshold'],
                    duration=config['duration'],
                    severity=config['severity'],
                    enabled=True
                )
                db.session.add(alert)
        
        db.session.commit()
```

#### C. Email Notifications for Critical Alerts

1. Enhanced Alert Notification
```python
class AlertNotifier:
    """Handle alert notifications with severity levels."""
    
    SEVERITY_LEVELS = {
        'critical': {
            'color': '#FF0000',
            'notify_interval': 300  # 5 minutes
        },
        'warning': {
            'color': '#FFA500',
            'notify_interval': 1800  # 30 minutes
        },
        'info': {
            'color': '#0000FF',
            'notify_interval': 3600  # 1 hour
        }
    }
    
    @staticmethod
    def format_alert_email(alert: MetricAlert, condition: AlertCondition) -> tuple:
        """Format alert email with severity-based styling."""
        severity = alert.severity or 'warning'
        color = AlertNotifier.SEVERITY_LEVELS[severity]['color']
        
        subject = f"[{severity.upper()}] System Alert: {alert.name}"
        
        body = f"""
<!DOCTYPE html>
<html>
<body>
    <div style="border-left: 4px solid {color}; padding-left: 10px;">
        <h2>System Alert Notification</h2>
        <p><strong>Alert Name:</strong> {alert.name}</p>
        <p><strong>Severity:</strong> {severity}</p>
        <p><strong>Metric:</strong> {alert.metric_name}</p>
        <p><strong>Condition:</strong> {alert.condition} {alert.threshold}</p>
        <p><strong>Current Value:</strong> {condition.current_value:.2f}</p>
        <p><strong>Triggered At:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
</body>
</html>
"""
        return subject, body
```

## Implementation Priority

### Immediate Tasks
1. Set up metric retention system
2. Configure default system health alerts
3. Implement basic trend analysis

### Short-term Tasks
1. Add alert severity levels
2. Enhance email notifications
3. Implement metric cleanup

### Long-term Tasks
1. Advanced trend analysis
2. Custom alert templates
3. Alert correlation

## Technical Notes

1. Database Considerations:
- Metric data partitioning
- Alert history retention
- Performance optimization

2. Performance Optimization:
- Metric aggregation
- Alert check batching
- Email notification queuing

3. Monitoring Improvements:
- Resource usage tracking
- Service health checks
- Network monitoring

## Testing Strategy

1. Unit Tests:
- Metric storage
- Alert conditions
- Trend analysis

2. Integration Tests:
- Alert notifications
- Metric cleanup
- Email formatting

3. Performance Tests:
- High-volume metrics
- Alert processing
- Database operations

## Migration Plan

1. Database Updates:
```sql
-- Add severity to alerts
ALTER TABLE metric_alert ADD COLUMN severity VARCHAR(32) DEFAULT 'warning';

-- Add index for metric cleanup
CREATE INDEX idx_metric_timestamp ON metric (timestamp);

-- Add alert history table
CREATE TABLE alert_history (
    id INTEGER PRIMARY KEY,
    alert_id INTEGER NOT NULL,
    triggered_at TIMESTAMP NOT NULL,
    value FLOAT NOT NULL,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by VARCHAR(64),
    FOREIGN KEY (alert_id) REFERENCES metric_alert(id)
);
```

2. Configuration Updates:
- Alert templates
- Notification settings
- Retention policies

## Security Considerations

1. Data Protection:
- Metric data encryption
- Alert access control
- Email security

2. Access Control:
- Alert management permissions
- Metric data access
- Notification settings

3. Compliance:
- Data retention policies
- Audit logging
- Alert documentation
