from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, UserActivity
from app.main import bp
from app.forms import LoginForm

@bp.route('/')
@login_required
def index():
    """Landing page after login."""
    return render_template('index.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            
            # Log the activity
            activity = UserActivity(
                user_id=user.id,
                username=user.username,
                activity="Logged in"
            )
            db.session.add(activity)
            db.session.commit()
            
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    if current_user.is_authenticated:
        # Log the activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity="Logged out"
        )
        db.session.add(activity)
        db.session.commit()
    
    logout_user()
    return redirect(url_for('main.login'))

@bp.route('/profile')
@login_required
def profile():
    """User profile page."""
    # Get user's recent activities
    activities = UserActivity.query.filter_by(
        user_id=current_user.id
    ).order_by(
        UserActivity.timestamp.desc()
    ).limit(10).all()
    
    return render_template('profile.html', activities=activities)
