from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, DateTimeField, BooleanField, FieldList
from wtforms.validators import DataRequired, Length, Optional, URL, ValidationError
from wtforms_sqlalchemy.fields import QuerySelectField
from app.models.user import User
from app.models.handoffs import WorkCenter, HandoffSettings, WorkCenterMember
from flask_login import current_user

def get_users():
    """Get all users for the assigned_to field."""
    return User.query.order_by(User.username).all()

def get_workcenters():
    """Get all workcenters."""
    return WorkCenter.query.order_by(WorkCenter.name).all()

def get_workcenter_members(workcenter_id):
    """Get all members of a workcenter."""
    return User.query.join(WorkCenterMember).filter(
        WorkCenterMember.workcenter_id == workcenter_id
    ).order_by(User.username).all()

class WorkCenterForm(FlaskForm):
    """Form for creating/editing workcenters"""
    name = StringField(
        'Work Center Name',
        validators=[DataRequired(), Length(max=100)],
        description='Enter the work center name'
    )
    description = TextAreaField(
        'Description',
        validators=[Optional(), Length(max=500)],
        description='Enter a description of the work center'
    )

class HandoffSettingsForm(FlaskForm):
    """Form for managing handoff settings"""
    workcenter = QuerySelectField(
        'Work Center',
        query_factory=get_workcenters,
        get_label='name',
        validators=[DataRequired()]
    )
    shifts = FieldList(
        StringField('Shift Name', validators=[DataRequired(), Length(max=100)]),
        min_entries=1,
        description='Enter shift names (e.g., Day Shift, Night Shift)'
    )
    require_close_comment = BooleanField(
        'Require Comment on Close',
        default=False,
        description='Require users to enter a comment when closing handoffs'
    )
    allow_close_with_comment = BooleanField(
        'Allow Close with Comment Option',
        default=True,
        description='Show both Close and Close with Comment buttons'
    )

class HandoffForm(FlaskForm):
    """Form for creating/editing handoffs"""
    ticket = StringField(
        'Ticket Number',
        validators=[DataRequired(), Length(max=100)],
        description='Enter the ticket number'
    )
    
    hostname = StringField(
        'Hostname',
        validators=[Optional(), Length(max=200)],
        description='Enter the hostname if applicable'
    )
    
    kirke = StringField(
        'Kirke',
        validators=[Optional(), Length(max=200)],
        description='Enter the Kirke tracking number if applicable'
    )
    
    priority = SelectField(
        'Priority',
        validators=[DataRequired()]
    )

    to_shift = SelectField(
        'To Shift',
        validators=[DataRequired()],
        description='Select the shift receiving the handoff'
    )
    
    due_date = DateTimeField(
        'Due Date',
        format='%Y-%m-%dT%H:%M',
        validators=[DataRequired()],
        description='Select the due date and time'
    )
    
    has_bridge = BooleanField(
        'Has Bridge',
        default=False,
        description='Check if there is a bridge link'
    )
    
    bridge_link = StringField(
        'Bridge Link',
        validators=[Optional(), URL()],
        description='Enter the bridge link if applicable'
    )
    
    description = TextAreaField(
        'Description',
        validators=[DataRequired(), Length(max=3000)],
        description='Enter the handoff description (max 3000 characters)'
    )

    def __init__(self, *args, **kwargs):
        super(HandoffForm, self).__init__(*args, **kwargs)
        
        # Get user's current workcenter
        user_workcenter = WorkCenter.query.join(WorkCenterMember).filter(
            WorkCenterMember.user_id == current_user.id
        ).first()
        
        if user_workcenter:
            # Get settings for the user's workcenter
            settings = HandoffSettings.get_settings(user_workcenter.id)
            
            # Update shifts choices
            self.to_shift.choices = [(s, s) for s in settings.shifts]
            
            # Update priority choices from settings
            self.priority.choices = [(p, p) for p in settings.priorities.keys()]

class HandoffCloseForm(FlaskForm):
    """Form for closing handoffs"""
    comment = TextAreaField(
        'Close Comment',
        validators=[Optional(), Length(max=1000)],
        description='Enter a comment about closing this handoff'
    )

    def __init__(self, *args, workcenter_id=None, **kwargs):
        super(HandoffCloseForm, self).__init__(*args, **kwargs)
        if workcenter_id:
            settings = HandoffSettings.get_settings(workcenter_id)
            if settings.require_close_comment:
                self.comment.validators = [DataRequired(), Length(max=1000)]

class HandoffStatusForm(FlaskForm):
    """Form for updating handoff status"""
    status = SelectField(
        'Status',
        choices=[
            ('Open', 'Open'),
            ('In Progress', 'In Progress'),
            ('Completed', 'Completed')
        ],
        validators=[DataRequired()]
    )
