"""Task view routes for the projects plugin."""

from flask import render_template
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.models import User
from ..models import Task, ProjectStatus, ProjectPriority
from app.plugins.projects import bp
from .tasks import get_available_tasks

@bp.route('/task/<int:task_id>/view', methods=['GET'])
@login_required
@requires_roles('user')
def view_task(task_id):
    """View a task"""
    task = Task.query.get_or_404(task_id)
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    available_tasks = get_available_tasks(task.project_id, task_id)
    
    # Check if user can edit
    can_edit = (
        current_user.has_role('admin') or
        task.project.lead_id == current_user.id or
        task.assigned_to_id == current_user.id
    )
    
    return render_template('projects/tasks/view.html', 
                         task=task,
                         users=users,
                         statuses=statuses,
                         priorities=priorities,
                         available_tasks=available_tasks,
                         can_edit=can_edit)

@bp.route('/task/<int:task_id>/edit', methods=['GET'])
@login_required
@requires_roles('user')
def edit_task(task_id):
    """Edit task view"""
    task = Task.query.get_or_404(task_id)
    
    # Check if user can edit
    if not (current_user.has_role('admin') or 
            task.project.lead_id == current_user.id or 
            task.assigned_to_id == current_user.id):
        return render_template('projects/tasks/view.html',
                            task=task,
                            error="You don't have permission to edit this task")
    
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    available_tasks = get_available_tasks(task.project_id, task_id)
    
    return render_template('projects/tasks/edit.html',
                         task=task,
                         users=users,
                         statuses=statuses,
                         priorities=priorities,
                         available_tasks=available_tasks)

@bp.route('/task/<int:task_id>/kanban', methods=['GET'])
@login_required
@requires_roles('user')
def task_kanban_view(task_id):
    """Kanban view for a task and its subtasks"""
    task = Task.query.get_or_404(task_id)
    users = User.query.all()
    statuses = ProjectStatus.query.all()
    priorities = ProjectPriority.query.all()
    
    # Group subtasks by status
    subtasks_by_status = {
        'todo': [],
        'in_progress': [],
        'review': [],
        'done': []
    }
    
    for subtask in task.subtasks:
        status = subtask.list_position or 'todo'
        if status not in subtasks_by_status:
            subtasks_by_status[status] = []
        subtasks_by_status[status].append(subtask)
    
    return render_template('projects/tasks/kanban.html',
                         task=task,
                         users=users,
                         statuses=statuses,
                         priorities=priorities,
                         subtasks_by_status=subtasks_by_status)

@bp.route('/task/<int:task_id>/timeline', methods=['GET'])
@login_required
@requires_roles('user')
def task_timeline_view(task_id):
    """Timeline view for a task's history"""
    task = Task.query.get_or_404(task_id)
    
    # Get all history entries for the task and its subtasks
    history_entries = []
    
    # Add task's own history
    history_entries.extend(task.history)
    
    # Add subtasks' history
    for subtask in task.subtasks:
        history_entries.extend(subtask.history)
    
    # Sort by created_at in descending order
    history_entries.sort(key=lambda x: x.created_at, reverse=True)
    
    return render_template('projects/tasks/timeline.html',
                         task=task,
                         history_entries=history_entries)

@bp.route('/task/<int:task_id>/dependencies-graph', methods=['GET'])
@login_required
@requires_roles('user')
def task_dependencies_graph(task_id):
    """Dependency graph view for a task"""
    task = Task.query.get_or_404(task_id)
    
    # Build nodes and edges for the dependency graph
    nodes = []
    edges = []
    visited = set()
    
    def add_task_to_graph(t, depth=0):
        if t.id in visited:
            return
        visited.add(t.id)
        
        # Add node
        nodes.append({
            'id': t.id,
            'label': t.name,
            'status': t.status.name if t.status else 'none',
            'depth': depth
        })
        
        # Add edges for dependencies
        for dep in t.dependencies:
            edges.append({
                'from': t.id,
                'to': dep.id,
                'type': 'depends_on'
            })
            add_task_to_graph(dep, depth + 1)
        
        # Add edges for dependent tasks
        for dep in t.dependent_tasks:
            edges.append({
                'from': dep.id,
                'to': t.id,
                'type': 'required_by'
            })
            add_task_to_graph(dep, depth + 1)
    
    add_task_to_graph(task)
    
    return render_template('projects/tasks/dependencies_graph.html',
                         task=task,
                         nodes=nodes,
                         edges=edges)
