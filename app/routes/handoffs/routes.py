from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.extensions import db
from datetime import datetime, timedelta
import json
from . import handoffs
from .forms import (
    HandoffForm, HandoffSettingsForm, HandoffStatusForm, 
    HandoffCloseForm, WorkCenterForm
)
from app.models.handoffs import HandoffSettings, Handoff, WorkCenter, WorkCenterMember
from app.models.user import User


def get_current_quarter_start():
    """Get the start date of the current quarter."""
    today = datetime.utcnow()
    month = today.month
    year = today.year
    quarter_month = ((month - 1) // 3) * 3 + 1
    return datetime(year, quarter_month, 1)

@handoffs.route('/')
@login_required
def index():
    """Display handoffs dashboard."""
    # Get user's current workcenter
    user_workcenter = WorkCenter.query.join(WorkCenterMember).filter(
        WorkCenterMember.user_id == current_user.id
    ).first()
    
    if not user_workcenter:
        flash('You are not assigned to any work centers.', 'warning')
        return redirect(url_for('handoffs.workcenter_list'))
    
    # Get settings for priorities
    settings = HandoffSettings.get_settings(user_workcenter.id)
    
    # Get all handoffs for the workcenter
    handoffs_list = Handoff.query.filter(
        Handoff.workcenter_id == user_workcenter.id
    ).order_by(Handoff.created_at.desc()).all()
    
    # Create form for the modal
    form = HandoffForm()
    
    return render_template('handoffs/index.html',
                         handoffs=handoffs_list,
                         priorities=settings.priorities,
                         settings=settings,
                         form=form)

@handoffs.route('/workcenter-list')
@login_required
@requires_permission('admin_handoffs_access', 'read')
def workcenter_list():
    """Display work centers list page."""
    workcenters = WorkCenter.query.all()
    return render_template('handoffs/workcenters.html',
                         workcenters=workcenters)

@handoffs.route('/workcenters/create', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_handoffs_access', 'write')
def create_workcenter():
    """Create a new work center."""
    form = WorkCenterForm()
    if form.validate_on_submit():
        workcenter = WorkCenter(
            name=form.name.data,
            description=form.description.data
        )
        db.session.add(workcenter)
        db.session.flush()  # Get the ID
        
        # Add creator as admin
        member = WorkCenterMember(
            workcenter_id=workcenter.id,
            user_id=current_user.id,
            is_admin=True
        )
        db.session.add(member)
        
        # Create default settings
        settings = HandoffSettings(
            workcenter_id=workcenter.id,
            priorities={
                "Low": "info",
                "Medium": "warning",
                "High": "danger"
            },
            shifts=["Day Shift", "Night Shift"],
            require_close_comment=False,
            allow_close_with_comment=True
        )
        db.session.add(settings)
        
        db.session.commit()
        flash('Work center created successfully.', 'success')
        return redirect(url_for('handoffs.workcenter_list'))
    return render_template('handoffs/workcenter_form.html', form=form)

@handoffs.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new handoff."""
    form = HandoffForm()
    
    # Get user's current workcenter
    user_workcenter = WorkCenter.query.join(WorkCenterMember).filter(
        WorkCenterMember.user_id == current_user.id
    ).first()
    
    if not user_workcenter:
        if request.is_json:
            return jsonify({'success': False, 'error': 'No work center assigned'})
        flash('You are not assigned to any work centers.', 'error')
        return redirect(url_for('handoffs.index'))
    
    if form.validate_on_submit():
        try:
            handoff = Handoff(
                workcenter_id=user_workcenter.id,  # Use current user's workcenter
                assigned_to_id=current_user.id,  # Assign to self
                created_by_id=current_user.id,
                ticket=form.ticket.data,
                hostname=form.hostname.data,
                kirke=form.kirke.data,
                priority=form.priority.data,
                from_shift="Self",  # Set a default value since column is not nullable
                to_shift=form.to_shift.data,
                has_bridge=form.has_bridge.data,
                bridge_link=form.bridge_link.data if form.has_bridge.data else None,
                description=form.description.data,
                due_date=form.due_date.data,
                status='Open'
            )
            
            db.session.add(handoff)
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True})
            
            flash('Handoff created successfully.', 'success')
            return redirect(url_for('handoffs.index'))
            
        except Exception as e:
            db.session.rollback()
            if request.is_json:
                return jsonify({'success': False, 'error': str(e)})
            flash(f'Error creating handoff: {str(e)}', 'error')
            return redirect(url_for('handoffs.index'))
    
    if request.is_json:
        errors = {}
        for field_name, field_errors in form.errors.items():
            errors[field_name] = field_errors
        return jsonify({'success': False, 'errors': errors})
    
    return render_template('handoffs/create.html', form=form)

@handoffs.route('/<int:id>/close', methods=['POST'])
@login_required
def close_handoff(id):
    """Close a handoff."""
    handoff = Handoff.query.get_or_404(id)
    settings = HandoffSettings.get_settings(handoff.workcenter_id)
    
    if settings.require_close_comment:
        form = HandoffCloseForm(workcenter_id=handoff.workcenter_id)
        if not form.validate_on_submit():
            flash('A close comment is required.', 'error')
            return redirect(url_for('handoffs.index'))
        handoff.close_comment = form.comment.data
    else:
        # Optional comment
        handoff.close_comment = request.form.get('comment')
    
    handoff.status = 'Completed'
    handoff.completed_at = datetime.utcnow()
    handoff.closed_by_id = current_user.id
    db.session.commit()
    
    flash('Handoff closed successfully.', 'success')
    return redirect(url_for('handoffs.index'))

@handoffs.route('/metrics')
@login_required
@requires_permission('view_metrics', 'read')
def metrics():
    """Display handoff metrics."""
    # Get selected workcenter
    workcenter_id = request.args.get('workcenter', type=int)
    if not workcenter_id:
        flash('Please select a work center.', 'warning')
        return redirect(url_for('handoffs.index'))
    
    # Get date range parameters
    start_date = request.args.get('start_date', None)
    end_date = request.args.get('end_date', None)
    
    # Base query
    query = Handoff.query.filter(Handoff.workcenter_id == workcenter_id)
    
    # Apply date filters if provided
    if start_date:
        query = query.filter(Handoff.created_at >= start_date)
    if end_date:
        query = query.filter(Handoff.created_at <= end_date)
    
    # Calculate metrics
    total_handoffs = query.count()
    completed_handoffs = query.filter(Handoff.status == 'Completed').count()
    overdue_handoffs = query.filter(
        Handoff.status != 'Completed',
        Handoff.due_date < datetime.utcnow()
    ).count()
    
    # Get handoffs by priority
    priority_stats = db.session.query(
        Handoff.priority,
        db.func.count(Handoff.id)
    ).filter(Handoff.workcenter_id == workcenter_id).group_by(Handoff.priority).all()
    
    # Get handoffs by assignee
    assignee_stats = db.session.query(
        Handoff.assigned_to_id,
        db.func.count(Handoff.id)
    ).filter(Handoff.workcenter_id == workcenter_id).group_by(Handoff.assigned_to_id).all()
    
    return render_template('handoffs/metrics.html',
                         total_handoffs=total_handoffs,
                         completed_handoffs=completed_handoffs,
                         overdue_handoffs=overdue_handoffs,
                         priority_stats=dict(priority_stats),
                         assignee_stats=dict(assignee_stats))

@handoffs.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_handoffs_access', 'write')
def admin_settings():
    """Admin page for managing handoff settings."""
    form = HandoffSettingsForm()
    
    if request.method == 'POST':
        if request.is_json:
            try:
                data = request.get_json()
                if not data:
                    return jsonify({'status': 'error', 'message': 'No data provided'}), 400
                
                workcenter_id = data.get('workcenter_id')
                if not workcenter_id:
                    return jsonify({'status': 'error', 'message': 'Workcenter ID required'}), 400
                
                settings = HandoffSettings.query.filter_by(workcenter_id=workcenter_id).first()
                if not settings:
                    settings = HandoffSettings(workcenter_id=workcenter_id)
                    db.session.add(settings)
                
                # Update settings from JSON data
                if 'shifts' in data:
                    # Ensure shifts is a list and contains only non-empty strings
                    shifts = [s.strip() for s in data['shifts'] if s.strip()]
                    settings.shifts = shifts
                
                if 'priorities' in data:
                    settings.priorities = data['priorities']
                
                if 'require_close_comment' in data:
                    settings.require_close_comment = data['require_close_comment']
                
                if 'allow_close_with_comment' in data:
                    settings.allow_close_with_comment = data['allow_close_with_comment']
                
                db.session.commit()
                return jsonify({'status': 'success'})
            except Exception as e:
                db.session.rollback()
                return jsonify({'status': 'error', 'message': str(e)}), 500
        else:
            # Handle form data submission
            if form.validate_on_submit():
                workcenter = form.workcenter.data
                settings = HandoffSettings.get_settings(workcenter.id)
                
                # Update settings
                settings.shifts = [shift.data for shift in form.shifts]
                settings.require_close_comment = form.require_close_comment.data
                settings.allow_close_with_comment = form.allow_close_with_comment.data
                
                try:
                    db.session.commit()
                    flash('Settings updated successfully.', 'success')
                    return redirect(url_for('handoffs.workcenter_list'))
                except Exception as e:
                    db.session.rollback()
                    flash(f'Error updating settings: {str(e)}', 'error')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{getattr(form, field).label.text}: {error}', 'error')
    
    return render_template('handoffs/admin_settings.html', form=form)

@handoffs.route('/admin/api/priorities', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_handoffs_access', 'write')
def update_priorities():
    """API endpoint to update priority settings."""
    if request.method == 'GET':
        workcenter_id = request.args.get('workcenter')
        if not workcenter_id:
            return jsonify({'error': 'Work center ID is required'}), 400
            
        settings = HandoffSettings.get_settings(workcenter_id)
        return jsonify({'priorities': settings.priorities})
    else:
        data = request.get_json()
        workcenter_id = data.get('workcenter_id')
        if not workcenter_id:
            return jsonify({'error': 'Work center ID is required'}), 400
            
        settings = HandoffSettings.get_settings(workcenter_id)
        settings.priorities = data.get('priorities')
        db.session.commit()
        return jsonify({'status': 'success'})

@handoffs.route('/api/shifts')
@login_required
def get_shifts():
    """API endpoint to get shifts for a work center."""
    workcenter_id = request.args.get('workcenter', type=int)
    if not workcenter_id:
        return jsonify({'error': 'Work center ID is required'}), 400
        
    settings = HandoffSettings.get_settings(workcenter_id)
    return jsonify({'shifts': settings.shifts})

@handoffs.route('/api/members')
@login_required
def get_members():
    """API endpoint to get members of a work center."""
    workcenter_id = request.args.get('workcenter', type=int)
    if not workcenter_id:
        return jsonify({'error': 'Work center ID is required'}), 400
        
    members = User.query.join(WorkCenterMember).filter(
        WorkCenterMember.workcenter_id == workcenter_id
    ).order_by(User.username).all()
    
    return jsonify({
        'members': [
            {
                'id': member.id,
                'username': member.username,
                'email': member.email
            }
            for member in members
        ]
    })
