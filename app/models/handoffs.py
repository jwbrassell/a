from app.extensions import db
from datetime import datetime

class WorkCenter(db.Model):
    __tablename__ = 'workcenters'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    settings = db.relationship('HandoffSettings', backref='workcenter', uselist=False)
    handoffs = db.relationship('Handoff', backref='workcenter')
    team_members = db.relationship('User', secondary='workcenter_members')

class WorkCenterMember(db.Model):
    __tablename__ = 'workcenter_members'
    
    id = db.Column(db.Integer, primary_key=True)
    workcenter_id = db.Column(db.Integer, db.ForeignKey('workcenters.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class HandoffSettings(db.Model):
    __tablename__ = 'handoff_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    workcenter_id = db.Column(db.Integer, db.ForeignKey('workcenters.id'), nullable=False)
    priorities = db.Column(db.JSON, nullable=False)  # Priority levels with their colors
    shifts = db.Column(db.JSON, nullable=False)  # List of shift names
    require_close_comment = db.Column(db.Boolean, default=False)
    allow_close_with_comment = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get_settings(workcenter_id):
        """Get the current handoff settings or create default ones if none exist."""
        settings = HandoffSettings.query.filter_by(workcenter_id=workcenter_id).first()
        if not settings:
            settings = HandoffSettings(
                workcenter_id=workcenter_id,
                priorities={
                    "Low": "info",
                    "Medium": "warning",
                    "High": "danger"
                },
                shifts=[
                    "Day Shift",
                    "Night Shift"
                ]
            )
            db.session.add(settings)
            db.session.commit()
        return settings

class Handoff(db.Model):
    __tablename__ = 'handoffs'
    
    id = db.Column(db.Integer, primary_key=True)
    workcenter_id = db.Column(db.Integer, db.ForeignKey('workcenters.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    closed_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ticket = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(200))
    kirke = db.Column(db.String(200))  # For Kirke tracking
    priority = db.Column(db.String(50), nullable=False)
    from_shift = db.Column(db.String(100))  # Made nullable
    to_shift = db.Column(db.String(100), nullable=False)
    has_bridge = db.Column(db.Boolean, default=False)
    bridge_link = db.Column(db.String(500))
    description = db.Column(db.Text, nullable=False)
    close_comment = db.Column(db.Text)
    due_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(50), default='Open')  # Open, In Progress, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='assigned_handoffs')
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='created_handoffs')
    closed_by = db.relationship('User', foreign_keys=[closed_by_id], backref='closed_handoffs')

    def to_dict(self):
        """Convert handoff to dictionary."""
        return {
            'id': self.id,
            'workcenter': self.workcenter.name,
            'assigned_to': self.assigned_to.username,
            'created_by': self.created_by.username,
            'closed_by': self.closed_by.username if self.closed_by else None,
            'ticket': self.ticket,
            'hostname': self.hostname,
            'kirke': self.kirke,
            'priority': self.priority,
            'from_shift': self.from_shift,
            'to_shift': self.to_shift,
            'has_bridge': self.has_bridge,
            'bridge_link': self.bridge_link,
            'description': self.description,
            'close_comment': self.close_comment,
            'due_date': self.due_date.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }

    @property
    def is_overdue(self):
        """Check if handoff is overdue."""
        if self.status != 'Completed' and self.due_date:
            return datetime.utcnow() > self.due_date
        return False
