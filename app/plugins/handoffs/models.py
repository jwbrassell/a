from datetime import datetime
from app import db
from flask_login import current_user

class Handoff(db.Model):
    """Model for tracking shift handovers."""
    __tablename__ = 'handoffs'
    
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to = db.Column(db.String(32), nullable=False)  # Shift assignment (1st, 2nd, 3rd)
    priority = db.Column(db.String(32), nullable=False)  # high, medium, low
    ticket = db.Column(db.String(100))
    hostname = db.Column(db.String(100))
    kirke = db.Column(db.String(100))
    due_date = db.Column(db.DateTime)
    has_bridge = db.Column(db.Boolean, default=False)
    bridge_link = db.Column(db.String(512))
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), default='open')  # open, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    closed_at = db.Column(db.DateTime)

    # Relationships
    reporter_user = db.relationship('User', backref='handoffs', lazy=True)

    def __repr__(self):
        return f'<Handoff {self.id}>'

    def to_dict(self):
        """Convert handoff to dictionary for DataTables."""
        return {
            'id': self.id,
            'assigned_to': self.assigned_to,
            'priority': self.priority,
            'ticket': self.ticket,
            'hostname': self.hostname,
            'kirke': self.kirke,
            'due_date': self.due_date.strftime('%Y-%m-%d %H:%M') if self.due_date else None,
            'has_bridge': self.has_bridge,
            'bridge_link': self.bridge_link,
            'description': self.description,
            'status': self.status,
            'reporter': self.reporter_user.username,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M'),
            'closed_at': self.closed_at.strftime('%Y-%m-%d %H:%M') if self.closed_at else None
        }

class HandoffShift(db.Model):
    """Model for managing handoff shifts."""
    __tablename__ = 'handoff_shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False, unique=True)  # 1st, 2nd, 3rd
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<HandoffShift {self.name}>'
