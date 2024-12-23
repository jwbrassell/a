from app.extensions import db
from datetime import datetime
from sqlalchemy import JSON

class DispatchSettings(db.Model):
    __tablename__ = 'dispatch_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    donotreply_email = db.Column(db.String(120), nullable=False)
    teams = db.Column(JSON, nullable=False)  # List of {name: str, email: str}
    priorities = db.Column(JSON, nullable=False)  # Priority levels with their colors
    subject_format = db.Column(db.String(200), nullable=False, default='[{priority}] {subject}')
    body_format = db.Column(db.Text, nullable=False, default='Dear {team},\n\n{message}\n\nBest regards,\n{requester}')
    signature = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings():
        """Get the current dispatch settings or create default ones if none exist."""
        settings = DispatchSettings.query.first()
        if not settings:
            settings = DispatchSettings(
                donotreply_email="donotreply@example.com",
                teams={"teams": []},  # Will be list of {name: str, email: str}
                priorities={
                    "Low": "info",
                    "Medium": "warning",
                    "High": "danger"
                },
                subject_format="[{priority}] {subject}",
                body_format="Dear {team},\n\n{message}\n\nBest regards,\n{requester}",
                signature=None
            )
            db.session.add(settings)
            db.session.commit()
        return settings

class DispatchHistory(db.Model):
    __tablename__ = 'dispatch_history'
    
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    priority = db.Column(db.String(50), nullable=False)
    team = db.Column(db.String(120), nullable=False)  # Store team name
    team_email = db.Column(db.String(120), nullable=False)  # Store team email
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New fields
    ticket_number = db.Column(db.String(100), nullable=False)
    ticket_number_2 = db.Column(db.String(100))
    rma_required = db.Column(db.Boolean, default=False)
    bridge_info = db.Column(db.String(200))
    rma_notes = db.Column(db.Text)
    due_date = db.Column(db.Date, nullable=False)
    hostname = db.Column(db.String(200), nullable=False)
    
    # Relationship to get requester details
    requester = db.relationship('User', backref='dispatch_requests')

    def to_dict(self):
        """Convert dispatch history to dictionary."""
        return {
            'id': self.id,
            'subject': self.subject,
            'message': self.message,
            'priority': self.priority,
            'team': self.team,
            'team_email': self.team_email,
            'requester': self.requester.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ticket_number': self.ticket_number,
            'ticket_number_2': self.ticket_number_2,
            'rma_required': self.rma_required,
            'bridge_info': self.bridge_info,
            'rma_notes': self.rma_notes,
            'due_date': self.due_date.strftime('%Y-%m-%d') if self.due_date else None,
            'hostname': self.hostname
        }
