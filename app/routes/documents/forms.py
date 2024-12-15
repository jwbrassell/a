from flask_wtf import FlaskForm
from wtforms import (
    StringField, TextAreaField, SelectField, SelectMultipleField, 
    BooleanField, RadioField, HiddenField
)
from wtforms.validators import DataRequired, Length, Optional

class DocumentForm(FlaskForm):
    """Form for creating/editing documents."""
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=1, max=256)
    ])
    content = TextAreaField('Content', validators=[DataRequired()])
    category = SelectField('Category', coerce=int)
    new_category = StringField('New Category')
    tags = SelectMultipleField('Tags', coerce=int)
    new_tags = StringField('New Tags (comma separated)')
    is_template = BooleanField('Save as Template')
    template_name = StringField('Template Name', validators=[Length(max=256)])
    is_private = BooleanField('Private Document')

class CategoryForm(FlaskForm):
    """Form for creating document categories."""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=64)
    ])
    description = StringField('Description', validators=[Length(max=256)])

class TagForm(FlaskForm):
    """Form for creating document tags."""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=1, max=64)
    ])

class DocumentShareForm(FlaskForm):
    """Form for sharing documents with users."""
    user = SelectField('User', coerce=int, validators=[DataRequired()])
    permission = RadioField('Permission Level', 
        choices=[
            ('read', 'Read Only'),
            ('write', 'Can Edit'),
            ('admin', 'Full Control')
        ],
        default='read'
    )

class DocumentSearchForm(FlaskForm):
    """Form for searching documents."""
    query = StringField('Search', validators=[Optional()])
    category = SelectField('Category', coerce=int, validators=[Optional()])
    tags = SelectMultipleField('Tags', coerce=int, validators=[Optional()])
    template_only = BooleanField('Templates Only')
    date_range = SelectField('Date Range',
        choices=[
            ('', 'Any Time'),
            ('today', 'Today'),
            ('week', 'Past Week'),
            ('month', 'Past Month'),
            ('year', 'Past Year')
        ],
        validators=[Optional()]
    )

class BulkActionForm(FlaskForm):
    """Form for bulk document operations."""
    action = SelectField('Action',
        choices=[
            ('categorize', 'Change Category'),
            ('delete', 'Delete Selected'),
            ('share', 'Share Selected'),
            ('export', 'Export Selected')
        ],
        validators=[DataRequired()]
    )
    category = SelectField('New Category', coerce=int, validators=[Optional()])
    user = SelectField('Share With User', coerce=int, validators=[Optional()])
    permission = SelectField('Permission Level',
        choices=[
            ('read', 'Read Only'),
            ('write', 'Can Edit'),
            ('admin', 'Full Control')
        ],
        validators=[Optional()]
    )
    export_format = SelectField('Export Format',
        choices=[
            ('pdf', 'PDF'),
            ('doc', 'Word Document')
        ],
        validators=[Optional()]
    )
    selected_docs = HiddenField('Selected Documents')

class DocumentFromTemplateForm(FlaskForm):
    """Form for creating a document from a template."""
    template = SelectField('Template', coerce=int, validators=[DataRequired()])
    title = StringField('New Document Title', validators=[
        DataRequired(),
        Length(min=1, max=256)
    ])
    category = SelectField('Category', coerce=int, validators=[DataRequired()])
    is_private = BooleanField('Private Document')
