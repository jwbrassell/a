from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField
from wtforms.validators import DataRequired, Length, Optional
from ..models import ProjectStatus, ProjectPriority

class ProjectForm(FlaskForm):
    """Form for creating/editing projects"""
    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    summary = StringField('Summary', validators=[Optional(), Length(max=500)])
    description = TextAreaField('Description')
    status = SelectField('Status')  # Choices set in __init__
    priority = SelectField('Priority')  # Choices set in __init__
    lead_id = SelectField('Lead', coerce=int)
    is_private = BooleanField('Private Project')
    notify_task_created = BooleanField('Task Creation Notifications')
    notify_task_completed = BooleanField('Task Completion Notifications')
    notify_comments = BooleanField('Comment Notifications')

    def __init__(self, *args, **kwargs):
        super(ProjectForm, self).__init__(*args, **kwargs)
        # Dynamically set status choices from database
        statuses = ProjectStatus.query.all()
        self.status.choices = [(s.name, s.name) for s in statuses] if statuses else [('Not Started', 'Not Started')]
        
        # Dynamically set priority choices from database
        priorities = ProjectPriority.query.all()
        self.priority.choices = [(p.name, p.name) for p in priorities] if priorities else [('Medium', 'Medium')]
        
        self.lead_id.choices = []  # Will be populated with users

    def populate_from_project(self, project):
        """Populate form with project data"""
        self.name.data = project.name
        self.summary.data = project.summary
        self.description.data = project.description
        self.status.data = project.status
        self.priority.data = project.priority
        self.lead_id.data = project.lead_id
        self.is_private.data = project.is_private
        self.notify_task_created.data = project.notify_task_created
        self.notify_task_completed.data = project.notify_task_completed
        self.notify_comments.data = project.notify_comments

    def update_project(self, project):
        """Update project with form data"""
        project.name = self.name.data
        project.summary = self.summary.data
        project.description = self.description.data
        project.status = self.status.data
        project.priority = self.priority.data
        project.lead_id = self.lead_id.data
        project.is_private = self.is_private.data
        project.notify_task_created = self.notify_task_created.data
        project.notify_task_completed = self.notify_task_completed.data
        project.notify_comments = self.notify_comments.data