from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, SelectMultipleField,
    DateField, BooleanField, IntegerField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class ProjectForm(FlaskForm):
    """Form for creating and editing projects"""
    name = StringField('Project Name', 
                      validators=[DataRequired(), Length(min=1, max=200)])
    summary = TextAreaField('Summary',
                          validators=[Optional(), Length(max=500)])
    icon = StringField('Font Awesome Icon',
                      validators=[Optional(), Length(max=50)])
    description = TextAreaField('Description')
    status = SelectField('Status', 
                        choices=[
                            ('planning', 'Planning'),
                            ('active', 'Active'),
                            ('on_hold', 'On Hold'),
                            ('completed', 'Completed')
                        ])
    priority = SelectField('Priority',
                         choices=[
                             ('low', 'Low'),
                             ('medium', 'Medium'),
                             ('high', 'High')
                         ],
                         default='medium')
    percent_complete = IntegerField('Percent Complete',
                                  validators=[NumberRange(min=0, max=100)],
                                  default=0)
    lead_id = SelectField('Project Lead', 
                         validators=[DataRequired()],
                         coerce=int)
    team_members = SelectMultipleField('Team Members',
                                     coerce=int)
    watchers = SelectMultipleField('Watchers',
                                  coerce=int)
    stakeholders = SelectMultipleField('Stakeholders',
                                     coerce=int)
    shareholders = SelectMultipleField('Shareholders',
                                     coerce=int)

class TaskForm(FlaskForm):
    """Form for creating and editing tasks"""
    name = StringField('Task Name',
                      validators=[DataRequired(), Length(min=1, max=200)])
    description = TextAreaField('Description')
    status = SelectField('Status',
                        choices=[
                            ('open', 'Open'),
                            ('in_progress', 'In Progress'),
                            ('review', 'Review'),
                            ('completed', 'Completed')
                        ])
    priority = SelectField('Priority',
                          choices=[
                              ('low', 'Low'),
                              ('medium', 'Medium'),
                              ('high', 'High')
                          ])
    assigned_to_id = SelectField('Assigned To',
                               validators=[Optional()],
                               coerce=int)
    due_date = DateField('Due Date',
                        validators=[Optional()])

class TodoForm(FlaskForm):
    """Form for creating and editing todos"""
    description = StringField('Description',
                            validators=[DataRequired(), Length(min=1, max=500)])
    assigned_to_id = SelectField('Assigned To',
                               validators=[Optional()],
                               coerce=int)
    completed = BooleanField('Completed')

class CommentForm(FlaskForm):
    """Form for adding comments"""
    content = TextAreaField('Comment',
                          validators=[DataRequired()])

class ProjectSettingsForm(FlaskForm):
    """Form for project settings"""
    notify_task_created = BooleanField('Task Creation Notifications')
    notify_task_completed = BooleanField('Task Completion Notifications')
    notify_comments = BooleanField('Comment Notifications')

    def populate_notification_settings(self, project):
        """Populate form with current notification settings"""
        self.notify_task_created.data = project.notify_task_created
        self.notify_task_completed.data = project.notify_task_completed
        self.notify_comments.data = project.notify_comments

    def update_notification_settings(self, project):
        """Update project with new notification settings"""
        project.notify_task_created = self.notify_task_created.data
        project.notify_task_completed = self.notify_task_completed.data
        project.notify_comments = self.notify_comments.data
