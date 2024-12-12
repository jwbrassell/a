"""Basic CRUD operations for projects."""

from flask import jsonify, request, render_template, url_for, redirect
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from sqlalchemy import or_
from datetime import datetime
from app.plugins.projects import bp
from ...models import Project, ProjectStatus, ProjectPriority, Todo, User, Role
from .utils import (
    can_edit_project,
    can_view_project,
    create_project_history,
    log_project_activity,
    track_project_changes,
    validate_project_data
)

@bp.route('/<int:project_id>', methods=['GET'])
@login_required
@requires_roles('user')
def view_project(project_id):
    """View project details"""
    project = Project.query.get_or_404(project_id)
    if not can_view_project(current_user, project):
        return redirect(url_for('main.index'))
    
    # Get all users for task assignment
    users = User.query.all()
    
    # Get statuses and priorities for task creation
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    return render_template(
        'projects/view.html',
        project=project,
        can_edit=can_edit_project(current_user, project),
        users=users,
        statuses=statuses,
        priorities=priorities
    )

@bp.route('/create', methods=['GET'])
@login_required
@requires_roles('user')
def create_project():
    """Create project form view"""
    # Get first available status and priority
    default_status = ProjectStatus.query.first()
    default_priority = ProjectPriority.query.first()
    
    if not default_status or not default_priority:
        return jsonify({
            'success': False,
            'message': 'Project status and priority configurations are missing. Please contact an administrator.'
        }), 500
    
    # Create a dummy project object for the template
    project = Project(
        name='',
        summary='',
        description='',
        status=default_status.name,
        priority=default_priority.name,
        percent_complete=0,
        lead_id=current_user.id,
        is_private=False,
        created_by=current_user.username
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
    print("Create project data:", data)  # Debug log
    
    # Validate project data for creation
    errors = validate_project_data(data, is_update=False)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Get first available status and priority if not provided
        if not data.get('status'):
            default_status = ProjectStatus.query.first()
            if not default_status:
                return jsonify({
                    'success': False,
                    'message': 'No project status configurations found. Please contact an administrator.'
                }), 500
            data['status'] = default_status.name
                
        if not data.get('priority'):
            default_priority = ProjectPriority.query.first()
            if not default_priority:
                return jsonify({
                    'success': False,
                    'message': 'No project priority configurations found. Please contact an administrator.'
                }), 500
            data['priority'] = default_priority.name
        
        # Validate status exists
        if not ProjectStatus.query.filter_by(name=data['status']).first():
            return jsonify({
                'success': False,
                'message': f'Invalid project status: {data["status"]}'
            }), 400
            
        # Validate priority exists
        if not ProjectPriority.query.filter_by(name=data['priority']).first():
            return jsonify({
                'success': False,
                'message': f'Invalid project priority: {data["priority"]}'
            }), 400
        
        # Create project with all fields
        project = Project(
            name=data['name'],
            summary=data.get('summary', ''),
            description=data.get('description', ''),
            status=data['status'],
            priority=data['priority'],
            icon=data.get('icon'),
            lead_id=current_user.id,
            is_private=data.get('is_private', False),
            created_by=current_user.username  # Ensure created_by is set
        )
        
        # Add watchers if provided
        if data.get('watchers'):
            watchers = User.query.filter(User.id.in_(data['watchers'])).all()
            project.watchers.extend(watchers)
            
        # Add stakeholders if provided
        if data.get('stakeholders'):
            stakeholders = User.query.filter(User.id.in_(data['stakeholders'])).all()
            project.stakeholders.extend(stakeholders)
            
        # Add shareholders if provided
        if data.get('shareholders'):
            shareholders = User.query.filter(User.id.in_(data['shareholders'])).all()
            project.shareholders.extend(shareholders)
            
        # Add roles if provided
        if data.get('roles'):
            roles = Role.query.filter(Role.name.in_(data['roles'])).all()
            project.roles.extend(roles)
        
        # Add todos if provided
        if data.get('todos'):
            for todo_data in data['todos']:
                if todo_data.get('description'):  # Only add todos with descriptions
                    # Convert date string to Python date object if provided
                    due_date = None
                    if todo_data.get('due_date'):
                        try:
                            due_date = datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Invalid date format for todo: {todo_data['due_date']}")
                    
                    todo = Todo(
                        description=todo_data['description'],
                        completed=todo_data.get('completed', False),
                        due_date=due_date,
                        sort_order=todo_data.get('sort_order', 0),
                        created_by=current_user.username  # Ensure created_by is set for todos
                    )
                    project.todos.append(todo)
        
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
        print(f"Error creating project: {str(e)}")  # Debug log
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
    
    # Base query for all projects
    query = Project.query
    
    # Apply search filter if provided
    if search:
        query = query.filter(or_(
            Project.name.ilike(f'%{search}%'),
            Project.summary.ilike(f'%{search}%'),
            Project.status.ilike(f'%{search}%')
        ))
    
    # Get total records before filtering
    total = query.count()
    
    # Apply pagination
    projects = query.order_by(Project.created_at.desc()).offset(start).limit(length).all()
    
    data = []
    for project in projects:
        if can_view_project(current_user, project):
            team_size = len(set([t.assigned_to_id for t in project.tasks if t.assigned_to_id]))
            total_tasks = len(project.tasks)
            completed_tasks = len([t for t in project.tasks if t.status and t.status.name == 'completed'])
            
            data.append({
                'id': project.id,
                'name': f'<a href="{url_for("projects.view_project", project_id=project.id)}">{project.name}</a>',
                'lead': project.lead.username if project.lead else 'Unassigned',
                'status': f'<span class="badge bg-{project.status_class}">{project.status}</span>',
                'team_size': team_size,
                'tasks': f'{completed_tasks}/{total_tasks}',
                'created': project.created_at.strftime('%Y-%m-%d'),
                'actions': render_template(
                    'projects/components/project_actions.html',
                    project=project,
                    current_user=current_user
                )
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
    print("Update project data:", data)  # Debug log
    
    # Validate project data with is_update=True
    errors = validate_project_data(data, is_update=True)
    if errors:
        return jsonify({
            'success': False,
            'message': errors[0]
        }), 400
    
    try:
        # Validate status exists if being updated
        if 'status' in data:
            if not ProjectStatus.query.filter_by(name=data['status']).first():
                return jsonify({
                    'success': False,
                    'message': f'Invalid project status: {data["status"]}'
                }), 400
                
        # Validate priority exists if being updated
        if 'priority' in data:
            if not ProjectPriority.query.filter_by(name=data['priority']).first():
                return jsonify({
                    'success': False,
                    'message': f'Invalid project priority: {data["priority"]}'
                }), 400
        
        # Update basic fields if provided
        if 'name' in data:
            project.name = data['name']
        if 'summary' in data:
            project.summary = data.get('summary', '')
        if 'description' in data:
            project.description = data.get('description', '')
        if 'status' in data:
            project.status = data['status']
        if 'priority' in data:
            project.priority = data['priority']
        if 'icon' in data:
            project.icon = data.get('icon')
        if 'is_private' in data:
            project.is_private = data.get('is_private', False)
        if 'percent_complete' in data:
            project.percent_complete = data.get('percent_complete', 0)
        
        # Update relationships if provided
        if 'watchers' in data:
            project.watchers = User.query.filter(User.id.in_(data['watchers'])).all()
        if 'stakeholders' in data:
            project.stakeholders = User.query.filter(User.id.in_(data['stakeholders'])).all()
        if 'shareholders' in data:
            project.shareholders = User.query.filter(User.id.in_(data['shareholders'])).all()
        if 'roles' in data:
            project.roles = Role.query.filter(Role.name.in_(data['roles'])).all()
        
        # Handle deleted todos first
        if 'deleted_todos' in data:
            print("Processing deleted todos:", data['deleted_todos'])
            for todo_id in data['deleted_todos']:
                Todo.query.filter_by(id=todo_id, project_id=project.id).delete()
        
        # Update remaining todos if provided
        if 'todos' in data:
            print("Processing todos:", data['todos'])
            
            # Get existing todo IDs
            existing_todo_ids = {str(todo.id) for todo in Todo.query.filter_by(project_id=project.id, task_id=None).all()}
            print("Existing todo IDs:", existing_todo_ids)
            
            # Track which todos we've processed
            processed_todo_ids = set()
            
            # Update or create todos
            for todo_data in data['todos']:
                if not todo_data.get('description'):  # Skip todos without descriptions
                    continue
                    
                todo_id = str(todo_data.get('id'))
                if todo_id and todo_id in existing_todo_ids:
                    # Update existing todo
                    todo = Todo.query.get(todo_id)
                    if todo:
                        todo.description = todo_data['description']
                        todo.completed = todo_data.get('completed', False)
                        if todo_data.get('due_date'):
                            try:
                                todo.due_date = datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date()
                            except ValueError:
                                print(f"Invalid date format for todo: {todo_data['due_date']}")
                        else:
                            todo.due_date = None
                        todo.sort_order = todo_data.get('sort_order', 0)
                        processed_todo_ids.add(todo_id)
                else:
                    # Create new todo
                    due_date = None
                    if todo_data.get('due_date'):
                        try:
                            due_date = datetime.strptime(todo_data['due_date'], '%Y-%m-%d').date()
                        except ValueError:
                            print(f"Invalid date format for todo: {todo_data['due_date']}")
                    
                    todo = Todo(
                        description=todo_data['description'],
                        completed=todo_data.get('completed', False),
                        due_date=due_date,
                        project_id=project.id,
                        task_id=None,  # Explicitly set task_id to None
                        sort_order=todo_data.get('sort_order', 0),
                        created_by=current_user.username  # Ensure created_by is set for new todos
                    )
                    print(f"Adding project todo: {todo.description}, due: {todo.due_date}")
                    db.session.add(todo)
            
            # Delete any remaining todos that weren't processed
            unprocessed_ids = existing_todo_ids - processed_todo_ids
            if unprocessed_ids:
                print("Deleting unprocessed todos:", unprocessed_ids)
                Todo.query.filter(Todo.id.in_(unprocessed_ids)).delete(synchronize_session=False)
        
        # Create history entry
        changes = track_project_changes(project, data)
        if changes:
            create_project_history(project, 'updated', current_user.id, changes)
            log_project_activity(current_user.id, current_user.username, "Updated", project.name)
        
        db.session.commit()
        print("Changes committed successfully")  # Debug log
        
        return jsonify({
            'success': True,
            'message': 'Project updated successfully',
            'project': project.to_dict()
        })
        
    except Exception as e:
        print(f"Error updating project: {str(e)}")  # Debug log
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
        print(f"Error deleting project: {str(e)}")  # Debug log
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
