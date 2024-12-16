"""Main routes for the projects plugin."""

from flask import render_template, request, jsonify, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_ as db_or_
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import Project, Task, ProjectStatus, ProjectPriority, db

logger = plugin.logger

def register_routes(blueprint):
    """Register routes with the provided blueprint."""
    global bp
    bp = blueprint

    @bp.route('/')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def index():
        """Main projects dashboard."""
        try:
            # Get all accessible projects
            projects = Project.query.all()
            
            # Get status and priority configurations
            statuses = ProjectStatus.query.all()
            priorities = ProjectPriority.query.all()
            
            # Get project statistics
            total_projects = len(projects)
            active_projects = sum(1 for p in projects if p.status != 'Completed')
            completed_projects = total_projects - active_projects
            
            # Get task statistics
            tasks = Task.query.filter(
                Task.project_id.in_([p.id for p in projects])
            ).all()
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status and t.status.name == 'Completed')
            
            # Calculate completion percentage
            completion_rate = (completed_projects / total_projects * 100) if total_projects > 0 else 0
            task_completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            plugin.log_action('view_dashboard', {
                'total_projects': total_projects,
                'active_projects': active_projects,
                'completed_projects': completed_projects,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks
            })
            
            return render_template('projects/index.html',
                                projects=projects,
                                statuses=statuses,
                                priorities=priorities,
                                total_projects=total_projects,
                                active_projects=active_projects,
                                completed_projects=completed_projects,
                                completion_rate=completion_rate,
                                total_tasks=total_tasks,
                                completed_tasks=completed_tasks,
                                task_completion_rate=task_completion_rate)
                                
        except Exception as e:
            logger.error(f"Error in projects dashboard: {str(e)}")
            raise

    @bp.route('/dashboard')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def dashboard():
        """Project analytics dashboard."""
        try:
            # Get project statistics by status
            status_stats = db.session.query(
                Project.status,
                db.func.count(Project.id)
            ).group_by(Project.status).all()
            
            # Get project statistics by priority
            priority_stats = db.session.query(
                Project.priority,
                db.func.count(Project.id)
            ).group_by(Project.priority).all()
            
            # Get task completion statistics
            task_stats = db.session.query(
                Task.status_id,
                db.func.count(Task.id)
            ).group_by(Task.status_id).all()
            
            # Format data for charts
            status_data = {
                'labels': [s[0] for s in status_stats if s[0]],
                'data': [s[1] for s in status_stats if s[0]]
            }
            
            priority_data = {
                'labels': [p[0] for p in priority_stats if p[0]],
                'data': [p[1] for p in priority_stats if p[0]]
            }
            
            task_data = {
                'labels': [ProjectStatus.query.get(s[0]).name for s in task_stats if s[0]],
                'data': [s[1] for s in task_stats if s[0]]
            }
            
            plugin.log_action('view_analytics', {
                'status_count': len(status_stats),
                'priority_count': len(priority_stats),
                'task_status_count': len(task_stats)
            })
            
            return render_template('projects/dashboard.html',
                                status_data=status_data,
                                priority_data=priority_data,
                                task_data=task_data)
                                
        except Exception as e:
            logger.error(f"Error in projects analytics: {str(e)}")
            raise

    @bp.route('/search')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def search():
        """Search projects and tasks."""
        try:
            query = request.args.get('q', '').strip()
            if not query:
                return jsonify([])
                
            # Search projects
            projects = Project.query.filter(
                db_or_(
                    Project.name.ilike(f'%{query}%'),
                    Project.summary.ilike(f'%{query}%'),
                    Project.description.ilike(f'%{query}%')
                )
            ).all()
            
            # Search tasks
            tasks = Task.query.filter(
                db_or_(
                    Task.name.ilike(f'%{query}%'),
                    Task.summary.ilike(f'%{query}%'),
                    Task.description.ilike(f'%{query}%')
                )
            ).all()
            
            # Format results
            results = []
            
            for project in projects:
                results.append({
                    'type': 'project',
                    'id': project.id,
                    'name': project.name,
                    'summary': project.summary,
                    'url': url_for('projects.view_project', id=project.id)
                })
                
            for task in tasks:
                results.append({
                    'type': 'task',
                    'id': task.id,
                    'name': task.name,
                    'summary': task.summary,
                    'project_id': task.project_id,
                    'url': url_for('projects.view_task', id=task.id)
                })
                
            plugin.log_action('search', {
                'query': query,
                'project_count': len(projects),
                'task_count': len(tasks)
            })
            
            return jsonify(results)
            
        except Exception as e:
            logger.error(f"Error in projects search: {str(e)}")
            raise
