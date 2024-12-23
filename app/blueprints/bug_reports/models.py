from datetime import datetime
from app.extensions import db
from app.models.user import User

class BugReport(db.Model):
    __tablename__ = 'bug_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    route = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    occurrence_type = db.Column(db.String(20), nullable=False)  # 'intermittent' or 'consistent'
    status = db.Column(db.String(20), default='open')  # open, solved, not_actionable, merged
    merged_with = db.Column(db.Integer, db.ForeignKey('bug_reports.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_roles = db.Column(db.String(500))  # Store as comma-separated string

    # Relationships
    user = db.relationship('User', backref=db.backref('bug_reports', lazy=True), primaryjoin='BugReport.user_id == User.id')
    screenshots = db.relationship('BugReportScreenshot', backref='bug_report', cascade='all, delete-orphan')

class BugReportScreenshot(db.Model):
    __tablename__ = 'bug_report_screenshots'
    
    id = db.Column(db.Integer, primary_key=True)
    bug_report_id = db.Column(db.Integer, db.ForeignKey('bug_reports.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
