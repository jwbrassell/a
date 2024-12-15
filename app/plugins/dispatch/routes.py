"""Route handlers for the dispatch plugin."""

from flask import render_template, flash, redirect, url_for, request, jsonify, current_app
from flask_login import login_required, current_user
from app.plugins.dispatch import bp
from app.plugins.dispatch.models import DispatchTeam, DispatchPriority, DispatchTransaction
from app.plugins.dispatch.utils.email_service import send_dispatch_email
from app import db
from app.models import UserActivity
from app.utils.activity_tracking import track_activity
from app.utils.enhanced_rbac import requires_permission
import logging

logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
@requires_permission('dispatch_access', 'read')
@track_activity
def index():
    """Main dispatch tool page with form and transactions table."""
    try:
        teams = DispatchTeam.query.all()
        priorities = DispatchPriority.query.all()
        return render_template('dispatch/index.html', teams=teams, priorities=priorities)
    except Exception as e:
        logger.error(f"Error loading dispatch index: {str(e)}")
        flash('Error loading dispatch tool', 'error')
        return redirect(url_for('main.index'))

@bp.route('/submit', methods=['POST'])
@login_required
@requires_permission('dispatch_access', 'write')
@track_activity
def submit():
    """Handle dispatch form submission."""
    try:
        # Create new transaction
        transaction = DispatchTransaction(
            team_id=request.form.get('team'),
            priority_id=request.form.get('priority'),
            description=request.form.get('description'),
            is_rma=bool(request.form.get('is_rma')),
            rma_info=request.form.get('rma_info'),
            is_bridge=bool(request.form.get('is_bridge')),
            bridge_link=request.form.get('bridge_link'),
            created_by_id=current_user.id
        )
        
        # Save to database
        db.session.add(transaction)
        db.session.commit()
        
        # Send email
        success, message = send_dispatch_email(transaction)
        if not success:
            transaction.status = 'failed'
            transaction.error_message = message
            db.session.commit()
            flash(f'Error sending dispatch request: {message}', 'error')
        else:
            # Log activity
            activity = UserActivity(
                user_id=current_user.id,
                username=current_user.username,
                activity=f"Created dispatch request to {transaction.team.name}"
            )
            db.session.add(activity)
            db.session.commit()
            flash('Dispatch request sent successfully', 'success')
            
        return redirect(url_for('dispatch.index'))
            
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in dispatch submit: {str(e)}")
        flash('An error occurred while processing your request', 'error')
        return redirect(url_for('dispatch.index'))

@bp.route('/transactions')
@login_required
@requires_permission('dispatch_access', 'read')
@track_activity
def get_transactions():
    """DataTables API endpoint for transactions."""
    try:
        # Get all transactions
        transactions = DispatchTransaction.query.order_by(DispatchTransaction.created_at.desc()).all()
        return jsonify({
            'data': [t.to_dict() for t in transactions]
        })
    except Exception as e:
        logger.error(f"Error fetching transactions: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/manage')
@login_required
@requires_permission('dispatch_manage_access', 'read')
@track_activity
def manage():
    """Management interface for teams and priorities."""
    try:
        teams = DispatchTeam.query.all()
        priorities = DispatchPriority.query.all()
        return render_template('dispatch/manage.html', teams=teams, priorities=priorities)
    except Exception as e:
        logger.error(f"Error loading manage page: {str(e)}")
        flash('Error loading management interface', 'error')
        return redirect(url_for('dispatch.index'))

@bp.route('/team', methods=['POST'])
@login_required
@requires_permission('dispatch_manage_access', 'write')
@track_activity
def add_team():
    """Add or update team."""
    try:
        team_id = request.form.get('id')
        if team_id:
            team = DispatchTeam.query.get_or_404(team_id)
            old_name = team.name
        else:
            team = DispatchTeam()
            old_name = None
            
        team.name = request.form.get('name')
        team.email = request.form.get('email')
        team.description = request.form.get('description')
        
        db.session.add(team)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"{'Updated' if old_name else 'Created'} dispatch team: {team.name}"
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Team saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving team: {str(e)}")
        flash(f'Error saving team: {str(e)}', 'error')
        
    return redirect(url_for('dispatch.manage'))

@bp.route('/priority', methods=['POST'])
@login_required
@requires_permission('dispatch_manage_access', 'write')
@track_activity
def add_priority():
    """Add or update priority."""
    try:
        priority_id = request.form.get('id')
        if priority_id:
            priority = DispatchPriority.query.get_or_404(priority_id)
            old_name = priority.name
        else:
            priority = DispatchPriority()
            old_name = None
            
        priority.name = request.form.get('name')
        priority.description = request.form.get('description')
        priority.color = request.form.get('color')
        priority.icon = request.form.get('icon')
        
        db.session.add(priority)
        
        # Log activity
        activity = UserActivity(
            user_id=current_user.id,
            username=current_user.username,
            activity=f"{'Updated' if old_name else 'Created'} dispatch priority: {priority.name}"
        )
        db.session.add(activity)
        db.session.commit()
        
        flash('Priority saved successfully', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving priority: {str(e)}")
        flash(f'Error saving priority: {str(e)}', 'error')
        
    return redirect(url_for('dispatch.manage'))
