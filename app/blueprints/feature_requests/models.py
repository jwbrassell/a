from datetime import datetime
from app.extensions import db
from sqlalchemy import JSON
from app.models.user import User

class FeatureRequest(db.Model):
    __tablename__ = 'feature_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    page_url = db.Column(db.String(500), nullable=False)
    screenshot_path = db.Column(db.String(500))
    status = db.Column(db.String(50), default='pending')  # pending, approved, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_feature_request_creator'), nullable=False)
    
    # Relationship with User model for creator
    creator = db.relationship('User', foreign_keys=[created_by], backref='feature_requests', lazy='joined')
    
    # Additional fields for the expanded section
    impact_details = db.Column(JSON)  # Stores the optional impact assessment details
    
    # Relationships
    votes = db.relationship('FeatureVote', backref='feature_request', lazy='dynamic')
    comments = db.relationship('FeatureComment', backref='feature_request', lazy='joined')

class FeatureVote(db.Model):
    __tablename__ = 'feature_votes'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_request_id = db.Column(db.Integer, db.ForeignKey('feature_requests.id', name='fk_feature_vote_request'), nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('feature_request_id', 'user_id', name='unique_feature_vote'),
    )

class FeatureComment(db.Model):
    __tablename__ = 'feature_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    feature_request_id = db.Column(db.Integer, db.ForeignKey('feature_requests.id', name='fk_feature_comment_request'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_feature_comment_user'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with User model
    user = db.relationship('User', foreign_keys=[user_id], backref='comments', lazy='joined')
