"""Forms for the dispatch plugin."""

from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, URL, Optional, ValidationError

class DispatchForm(FlaskForm):
    """Form for creating dispatch transactions."""
    team = SelectField('Team', 
        validators=[DataRequired()],
        coerce=int
    )
    
    priority = SelectField('Priority',
        validators=[DataRequired()],
        coerce=int
    )
    
    description = TextAreaField('Description',
        validators=[
            DataRequired(),
            Length(min=1, max=2000, message='Description must be between 1 and 2000 characters')
        ]
    )
    
    is_rma = BooleanField('Is RMA')
    
    rma_info = TextAreaField('RMA Information',
        validators=[
            Optional(),
            Length(max=1000, message='RMA information must not exceed 1000 characters')
        ]
    )
    
    is_bridge = BooleanField('Has Bridge')
    
    bridge_link = StringField('Bridge Link',
        validators=[
            Optional(),
            URL(message='Please enter a valid URL'),
            Length(max=512, message='Bridge link must not exceed 512 characters')
        ]
    )
    
    submit = SubmitField('Send Dispatch')

    def validate_bridge_link(self, field):
        """Validate bridge link is provided if is_bridge is checked."""
        if self.is_bridge.data and not field.data:
            raise ValidationError('Bridge link is required when bridge is enabled')

    def validate_rma_info(self, field):
        """Validate RMA info is provided if is_rma is checked."""
        if self.is_rma.data and not field.data:
            raise ValidationError('RMA information is required when RMA is enabled')

class TeamForm(FlaskForm):
    """Form for managing dispatch teams."""
    name = StringField('Team Name',
        validators=[
            DataRequired(),
            Length(min=1, max=64, message='Team name must be between 1 and 64 characters')
        ]
    )
    
    email = StringField('Team Email',
        validators=[
            DataRequired(),
            Email(message='Please enter a valid email address'),
            Length(max=120, message='Email must not exceed 120 characters')
        ]
    )
    
    description = TextAreaField('Description',
        validators=[
            Optional(),
            Length(max=256, message='Description must not exceed 256 characters')
        ]
    )
    
    submit = SubmitField('Save Team')

class PriorityForm(FlaskForm):
    """Form for managing dispatch priorities."""
    name = StringField('Priority Name',
        validators=[
            DataRequired(),
            Length(min=1, max=32, message='Priority name must be between 1 and 32 characters')
        ]
    )
    
    description = TextAreaField('Description',
        validators=[
            Optional(),
            Length(max=256, message='Description must not exceed 256 characters')
        ]
    )
    
    color = StringField('Color',
        validators=[
            DataRequired(),
            Length(min=7, max=7, message='Color must be a valid hex code (e.g. #FF0000)'),
        ]
    )
    
    icon = StringField('Icon Class',
        validators=[
            DataRequired(),
            Length(min=1, max=32, message='Icon class must be between 1 and 32 characters')
        ]
    )
    
    submit = SubmitField('Save Priority')

    def validate_color(self, field):
        """Validate color is a valid hex code."""
        if not field.data.startswith('#'):
            raise ValidationError('Color must start with #')
        try:
            int(field.data[1:], 16)
        except ValueError:
            raise ValidationError('Color must be a valid hex code (e.g. #FF0000)')
