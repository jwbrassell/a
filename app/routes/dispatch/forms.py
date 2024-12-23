from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, EmailField, DateField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

class DispatchSettingsForm(FlaskForm):
    donotreply_email = EmailField('Do Not Reply Email', 
                                 validators=[DataRequired(), Email()])
    subject_format = StringField('Subject Format',
                               validators=[DataRequired()],
                               description='Available variables: {priority}, {subject}')
    body_format = TextAreaField('Email Body Format',
                              validators=[DataRequired()],
                              description='Available variables: {team}, {message}, {requester}')
    signature = TextAreaField('Email Signature',
                            description='Optional signature to append to all emails')
    
    # Note: The teams and priorities will be handled via AJAX in the frontend
    # since they're dynamic fields that need to be added/removed

class DispatchRequestForm(FlaskForm):
    subject = StringField('Subject', 
                         validators=[DataRequired(), Length(max=200)])
    message = TextAreaField('Message', 
                          validators=[DataRequired()])
    priority = SelectField('Priority',
                         validators=[DataRequired()],
                         choices=[])  # Choices populated from settings
    team = SelectField('Team',
                      validators=[DataRequired()],
                      choices=[])  # Choices populated from settings
    ticket_number = StringField('Ticket Number',
                            validators=[DataRequired()])
    ticket_number_2 = StringField('Ticket Number 2',
                               validators=[Optional()])
    rma_required = BooleanField('RMA Required')
    bridge_info = StringField('Bridge Information',
                          validators=[Optional()])
    rma_notes = TextAreaField('RMA Notes',
                           validators=[Optional()])
    due_date = DateField('Due Date',
                      validators=[DataRequired()])
    hostname = StringField('Hostname',
                       validators=[DataRequired()])

class TeamForm(FlaskForm):
    """Form for individual team entries (used in JavaScript)"""
    name = StringField('Team Name', validators=[DataRequired()])
    email = EmailField('Team Email', validators=[DataRequired(), Email()])
