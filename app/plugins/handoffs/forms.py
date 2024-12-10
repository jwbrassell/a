from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, URLField, DateTimeField
from wtforms.validators import DataRequired, URL, Optional, Length
from datetime import datetime

class HandoffForm(FlaskForm):
    """Form for creating and editing handoffs."""
    
    assigned_to = SelectField('Assigned To',
                            choices=[
                                ('', 'Select shift'),
                                ('1st', '1st Shift'),
                                ('2nd', '2nd Shift'),
                                ('3rd', '3rd Shift')
                            ],
                            validators=[DataRequired()])
    
    priority = SelectField('Priority', 
                         choices=[
                             ('', 'Select priority'),
                             ('high', 'High'), 
                             ('medium', 'Medium'), 
                             ('low', 'Low')
                         ],
                         validators=[DataRequired()])
    
    ticket = StringField('Ticket Number', 
                        validators=[Optional(), Length(max=100)])
    
    hostname = StringField('Hostname', 
                         validators=[Optional(), Length(max=100)])
    
    kirke = StringField('KIRKE', 
                       validators=[Optional(), Length(max=100)])
    
    due_date = DateTimeField('Due Date',
                           format='%Y-%m-%dT%H:%M',  # Format for HTML5 datetime-local input
                           validators=[Optional()])
    
    has_bridge = BooleanField('Has Bridge?')
    
    bridge_link = URLField('Bridge Link', 
                         validators=[Optional(), URL()],
                         render_kw={'placeholder': 'https://...'})
    
    description = TextAreaField('Description', 
                              validators=[DataRequired(), Length(max=300)],
                              render_kw={'rows': 5, 
                                       'placeholder': 'Notes: Max length 300 characters only'})

    def __init__(self, *args, **kwargs):
        super(HandoffForm, self).__init__(*args, **kwargs)
        if isinstance(self.due_date.data, str):
            try:
                self.due_date.data = datetime.strptime(self.due_date.data, '%Y-%m-%dT%H:%M')
            except (ValueError, TypeError):
                self.due_date.data = None
