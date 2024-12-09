"""Basic CRUD operations for projects."""

from flask import jsonify, request, render_template, url_for, redirect
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from sqlalchemy import or_
from app.plugins.projects import bp
from ...models import Project, ProjectStatus, ProjectPriority
from .utils import (
    can_edit_project,
    can_view_project,
    create_project_history,
    log_project_activity,
    track_project_changes,
    validate_project_data
)

@bp.route('/create', methods=['GET'])
@login_required
@requires_roles('user')
def create_project():
    """Create project form view"""
    # Create a dummy project object for the template
    project = Project(
        name='',
        summary='',
        description='',
        status='new',
        priority='medium',
        percent_complete=0,
        lead_id=current_user.id,
        is_private=False
    )
    
    # Initialize relationships as empty lists
    project.tasks = []
    project.todos = []
    project.comments = []
    project.history = []
    project.watchers = []
    project.stakeholders = []
    project.shareholders = []
    project.roles = []
    
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    return render_template(
        'projects/create.html',
        project=project,
        statuses=statuses,
        priorities=priorities
    )

@bp.route('/create', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_project_post():
    """Create a new project"""
    data = request.get_json()
    
    # Validate project data
    errors = validate_project_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        project = Project(
            name=data['name'],
            summary=data.get('summary', ''),
            description=data.get('description', ''),
            status=data.get('status', 'new'),
            priority=data.get('priority', 'medium'),
            lead_id=current_user.id
        )
        
        # Create history entry
        create_project_history(project, 'created', current_user.id)
        
        # Log activity
        log_project_activity(current_user.id, current_user.username, "Created", project.name)
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project created successfully',
            'project': project.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/list')
@login_required
@requires_roles('user')
def list_projects():
    """Get projects for DataTables"""
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', type=int, default=0)
    length = request.args.get('length', type=int, default=10)
    search = request.args.get('search[value]', type=str, default='')
    status = request.args.get('status', type=str)
    
    query = Project.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Project.name.ilike(f'%{search}%'))
    
    total = query.count()
    projects = query.offset(start).limit(length).all()
    
    data = []
    for project in projects:
        if can_view_project(current_user, project):
            team_size = len(set([t.assigned_to_id for t in project.tasks if t.assigned_to_id]))
            total_tasks = len(project.tasks)
            completed_tasks = len([t for t in project.tasks if t.status == 'completed'])
            
            data.append({
                'id': project.id,
                'name': f'<a href="{url_for("projects.view_project", project_id=project.id)}">{project.name}</a>',
                'lead': project.lead.username if project.lead else 'Unassigned',
                'status': f'<span class="badge badge-{project.status_obj.color if project.status_obj else "secondary"}">{project.status}</span>',
                'team_size': team_size,
                'tasks': f'{completed_tasks}/{total_tasks}',
                'created': project.created_at.strftime('%Y-%m-%d'),
                'actions': render_template('projects/components/project_actions.html', project=project)
            })
    
    return jsonify({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': data
    })

@bp.route('/<int:project_id>/edit', methods=['GET'])
@login_required
@requires_roles('user')
def edit_project(project_id):
    """Edit project form view"""
    project = Project.query.get_or_404(project_id)
    if not can_edit_project(current_user, project):
        return redirect(url_for('projects.view_project', project_id=project_id))
    
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    return render_template(
        'projects/edit.html',
        project=project,
        statuses=statuses,
        priorities=priorities
    )

@bp.route('/<int:project_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_project(project_id):
    """Update a project"""
    project = Project.query.get_or_404(project_id)
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to edit this project'
        }), 403
    
    data = request.get_json()
    
    # Validate project data
    errors = validate_project_data(data)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Track changes
        changes = track_project_changes(project, data)
        
        if changes:
            # Update project fields
            for field, change in changes.items():
                setattr(project, field, change['new'])
            
            # Create history entry
            create_project_history(project, 'updated', current_user.id, changes)
            
            # Log activity
            log_project_activity(current_user.id, current_user.username, "Updated", project.name)
            
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'project': project.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@bp.route('/<int:project_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_project(project_id):
    """Delete a project"""
    project = Project.query.get_or_404(project_id)
    if not can_edit_project(current_user, project):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to delete this project'
        }), 403
    
    try:
        project_name = project.name
        
        # Create history entry
        create_project_history(project, 'deleted', current_user.id)
        
        # Log activity
        log_project_activity(current_user.id, current_user.username, "Deleted", project_name)
        
        db.session.delete(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Project deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
