from flask import render_template, flash, redirect, url_for, request, jsonify
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.extensions import db
from app.utils.email_service import send_notification_email
from . import dispatch
from .forms import DispatchSettingsForm, DispatchRequestForm
from app.models.dispatch import DispatchSettings, DispatchHistory

@dispatch.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@requires_permission('admin_dispatch_access', 'write')
def admin_settings():
    """Admin page for managing dispatch settings."""
    settings = DispatchSettings.get_settings()
    form = DispatchSettingsForm()
    
    if form.validate_on_submit():
        settings.donotreply_email = form.donotreply_email.data
        settings.subject_format = form.subject_format.data
        settings.body_format = form.body_format.data
        settings.signature = form.signature.data
        db.session.commit()
        flash('Settings updated successfully.', 'success')
        return redirect(url_for('dispatch.admin_settings'))
        
    # Pre-populate form
    if request.method == 'GET':
        form.donotreply_email.data = settings.donotreply_email
        form.subject_format.data = settings.subject_format
        form.body_format.data = settings.body_format
        form.signature.data = settings.signature
        
    return render_template('dispatch/admin_settings.html', 
                         form=form, 
                         settings=settings)

@dispatch.route('/admin/api/teams', methods=['POST'])
@login_required
@requires_permission('admin_dispatch_access', 'write')
def update_teams():
    """API endpoint to update team settings."""
    data = request.get_json()
    if not isinstance(data.get('teams'), list):
        return jsonify({'status': 'error', 'message': 'Invalid data format'}), 400
    
    settings = DispatchSettings.get_settings()
    settings.teams = data
    db.session.commit()
    return jsonify({'status': 'success'})

@dispatch.route('/admin/api/priorities', methods=['POST'])
@login_required
@requires_permission('admin_dispatch_access', 'write')
def update_priorities():
    """API endpoint to update priority settings."""
    data = request.get_json()
    settings = DispatchSettings.get_settings()
    settings.priorities = data
    db.session.commit()
    return jsonify({'status': 'success'})

@dispatch.route('/', methods=['GET', 'POST'])
@login_required
def dispatch_request():
    """Main dispatch request page with form and history."""
    settings = DispatchSettings.get_settings()
    form = DispatchRequestForm()
    
    # Populate form choices
    form.priority.choices = [(k, k) for k in settings.priorities.keys()]
    form.team.choices = [(team['name'], f"{team['name']} ({team['email']})") 
                        for team in settings.teams.get('teams', [])]
    
    if form.validate_on_submit():
        # Get team email from settings
        team_data = next((team for team in settings.teams['teams'] 
                         if team['name'] == form.team.data), None)
        if not team_data:
            flash('Selected team not found.', 'error')
            return redirect(url_for('dispatch.dispatch_request'))

        # Create history record
        history = DispatchHistory(
            subject=form.subject.data,
            message=form.message.data,
            priority=form.priority.data,
            team=team_data['name'],
            team_email=team_data['email'],
            requester_id=current_user.id,
            # New fields
            ticket_number=form.ticket_number.data,
            ticket_number_2=form.ticket_number_2.data,
            rma_required=form.rma_required.data,
            bridge_info=form.bridge_info.data if form.rma_required.data else None,
            rma_notes=form.rma_notes.data if form.rma_required.data else None,
            due_date=form.due_date.data,
            hostname=form.hostname.data
        )
        db.session.add(history)
        
        # Format email content
        subject = settings.subject_format.format(
            priority=form.priority.data,
            subject=form.subject.data
        )
        
        # Enhanced email body with new fields
        body = f"""
Team: {team_data['name']}
Priority: {form.priority.data}
Ticket Number: {form.ticket_number.data}
{f'Ticket Number 2: {form.ticket_number_2.data}' if form.ticket_number_2.data else ''}
Due Date: {form.due_date.data.strftime('%Y-%m-%d')}
Hostname: {form.hostname.data}

{f'RMA Required: Yes' if form.rma_required.data else 'RMA Required: No'}
{f'Bridge Information: {form.bridge_info.data}' if form.rma_required.data and form.bridge_info.data else ''}
{f'RMA Notes: {form.rma_notes.data}' if form.rma_required.data and form.rma_notes.data else ''}

Description:
{form.message.data}

Requester: {current_user.name}
"""
        
        if settings.signature:
            body = f"{body}\n\n{settings.signature}"
        
        # Send email
        send_notification_email(
            subject=subject,
            body=body,
            recipients=[team_data['email']]
        )
        
        db.session.commit()
        flash('Dispatch request sent successfully.', 'success')
        return redirect(url_for('dispatch.dispatch_request'))
        
    # Get history for display
    history = DispatchHistory.query.order_by(DispatchHistory.created_at.desc()).all()
    
    return render_template('dispatch/request.html',
                         form=form,
                         history=history,
                         priorities=settings.priorities)

@dispatch.route('/api/history')
@login_required
def get_history():
    """API endpoint to get dispatch history."""
    history = DispatchHistory.query.order_by(DispatchHistory.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])
