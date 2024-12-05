from datetime import datetime
from app import db
from flask_login import current_user

class DispatchTeam(db.Model):
    __tablename__ = 'dispatch_teams'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    transactions = db.relationship('DispatchTransaction', backref='team', lazy='dynamic')

    def __repr__(self):
        return f'<DispatchTeam {self.name}>'

class DispatchPriority(db.Model):
    __tablename__ = 'dispatch_priorities'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.String(256))
    color = db.Column(db.String(7), default='#000000')  # Hex color code
    icon = db.Column(db.String(32), default='fa-circle')  # FontAwesome icon class
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    transactions = db.relationship('DispatchTransaction', backref='priority', lazy='dynamic')

    def __repr__(self):
        return f'<DispatchPriority {self.name}>'

class DispatchTransaction(db.Model):
    __tablename__ = 'dispatch_transactions'
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('dispatch_teams.id'), nullable=False)
    priority_id = db.Column(db.Integer, db.ForeignKey('dispatch_priorities.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_rma = db.Column(db.Boolean, default=False)
    rma_info = db.Column(db.Text)
    is_bridge = db.Column(db.Boolean, default=False)
    bridge_link = db.Column(db.String(512))
    status = db.Column(db.String(32), default='sent')  # sent, failed
    error_message = db.Column(db.Text)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<DispatchTransaction {self.id}>'

    @property
    def created_by_name(self):
        from app.models import User
        user = User.query.get(self.created_by_id)
        return user.name if user else 'Unknown'

    def to_dict(self):
        """Convert transaction to dictionary for DataTables"""
        return {
            'id': self.id,
            'team': self.team.name,
            'priority': self.priority.name,
            'description': self.description,
            'created_by': self.created_by_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status
        }
