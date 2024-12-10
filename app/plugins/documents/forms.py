from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, Length

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
