from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField
from wtforms.validators import DataRequired, URL, Length

class WebLinkForm(FlaskForm):
    """Form for creating/editing web links."""
    url = StringField('URL', validators=[
        DataRequired(),
        URL(message="Please enter a valid URL"),
        Length(max=500)
    ])
    friendly_name = StringField('Friendly Name', validators=[
        DataRequired(),
        Length(min=1, max=200, message="Name must be between 1 and 200 characters")
    ])
    notes = TextAreaField('Notes')
    icon = StringField('Font Awesome Icon', validators=[
        Length(max=100, message="Icon class must be less than 100 characters")
    ])
    category = SelectField('Category', coerce=int)
    tags = SelectMultipleField('Tags', coerce=int)

class CategoryForm(FlaskForm):
    """Form for creating web link categories."""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Category name must be between 1 and 100 characters")
    ])

class TagForm(FlaskForm):
    """Form for creating web link tags."""
    name = StringField('Tag Name', validators=[
        DataRequired(),
        Length(min=1, max=100, message="Tag name must be between 1 and 100 characters")
    ])
