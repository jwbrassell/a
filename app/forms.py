from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, SelectMultipleField, FileField, SearchField
from wtforms.validators import DataRequired, Length, ValidationError
from flask_wtf.file import FileAllowed, FileSize

class LoginForm(FlaskForm):
    """Form for LDAP authentication."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class DocumentForm(FlaskForm):
    """Form for creating and editing documents."""
    title = StringField('Title', validators=[
        DataRequired(),
        Length(min=1, max=256, message='Title must be between 1 and 256 characters')
    ])
    
    content = TextAreaField('Content', validators=[DataRequired()])
    
    category_id = SelectField('Category', 
        validators=[DataRequired()],
        coerce=int
    )
    
    tags = SelectMultipleField('Tags',
        coerce=int
    )
    
    files = FileField('Attach Files', 
        validators=[
            FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx'], 
                       'Only images and documents are allowed!'),
            FileSize(max_size=20 * 1024 * 1024)  # 20MB limit
        ]
    )
    
    submit = SubmitField('Save Document')

class DocumentCategoryForm(FlaskForm):
    """Form for creating and editing document categories."""
    name = StringField('Category Name', validators=[
        DataRequired(),
        Length(min=1, max=128, message='Category name must be between 1 and 128 characters')
    ])
    description = StringField('Description', validators=[
        Length(max=256, message='Description must not exceed 256 characters')
    ])
    submit = SubmitField('Save Category')

class TagForm(FlaskForm):
    """Form for creating tags."""
    name = StringField('Tag Name', validators=[
        DataRequired(),
        Length(min=1, max=64, message='Tag name must be between 1 and 64 characters')
    ])
    submit = SubmitField('Create Tag')

class DocumentSearchForm(FlaskForm):
    """Form for searching documents."""
    query = SearchField('Search', validators=[
        Length(max=100, message='Search query must not exceed 100 characters')
    ])
    category = SelectField('Category', coerce=int, choices=[(0, 'All Categories')])
    submit = SubmitField('Search')
