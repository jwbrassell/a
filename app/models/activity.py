"""Activity tracking models."""
from datetime import datetime
from app.extensions import db

class UserActivity(db.Model):
    """Model for tracking user activities."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    action = db.Column(db.String(64))  # e.g., 'add_member', 'remove_member'
    resource = db.Column(db.String(128))  # e.g., 'role_1', 'user_2'
    details = db.Column(db.String(512))  # Detailed description of the activity
    activity = db.Column(db.String(512), nullable=False)  # Keep for backward compatibility
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<UserActivity {self.username}: {self.activity}>'

    @property
    def description(self):
        """Get a human-readable description of the activity."""
        return self.details or self.activity

class PageVisit(db.Model):
    """Model for tracking page visits."""
    id = db.Column(db.Integer, primary_key=True)
    route = db.Column(db.String(256), nullable=False)
    method = db.Column(db.String(10), nullable=False)
    status_code = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    username = db.Column(db.String(64))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(256))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PageVisit {self.route}>'
