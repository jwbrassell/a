"""Comment management routes for the projects plugin."""

from flask import render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from app.utils.enhanced_rbac import requires_permission
from app.utils.plugin_base import plugin_error_handler
from . import bp, plugin
from .models import Project, Task, Comment, History
from app import db

logger = plugin.logger

def register_routes(blueprint):
    """Register routes with the provided blueprint."""
    global bp
    bp = blueprint

    @bp.route('/projects/<int:project_id>/comments')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def list_project_comments(project_id):
        """List all comments for a project."""
        try:
            project = Project.query.get_or_404(project_id)
            comments = Comment.query.filter_by(
                project_id=project_id
            ).order_by(Comment.created_at.desc()).all()
            
            plugin.log_action('list_project_comments', {
                'project_id': project_id,
                'comment_count': len(comments)
            })
            
            return render_template('projects/comments/list.html',
                                project=project,
                                comments=comments)
                                
        except Exception as e:
            logger.error(f"Error listing comments for project {project_id}: {str(e)}")
            raise

    @bp.route('/tasks/<int:task_id>/comments')
    @login_required
    @requires_permission('projects_access', 'read')
    @plugin_error_handler
    def list_task_comments(task_id):
        """List all comments for a task."""
        try:
            task = Task.query.get_or_404(task_id)
            comments = Comment.query.filter_by(
                task_id=task_id
            ).order_by(Comment.created_at.desc()).all()
            
            plugin.log_action('list_task_comments', {
                'task_id': task_id,
                'comment_count': len(comments)
            })
            
            return render_template('projects/comments/list.html',
                                task=task,
                                comments=comments)
                                
        except Exception as e:
            logger.error(f"Error listing comments for task {task_id}: {str(e)}")
            raise

    @bp.route('/projects/<int:project_id>/comments/add', methods=['POST'])
    @login_required
    @requires_permission('projects_comment', 'write')
    @plugin_error_handler
    def add_project_comment(project_id):
        """Add a comment to a project."""
        try:
            project = Project.query.get_or_404(project_id)
            
            # Create comment
            comment = Comment(
                project_id=project_id,
                content=request.form['content'],
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(comment)
            
            # Add history entry
            history = History(
                entity_type='comment',
                project_id=project_id,
                action='created',
                details={
                    'content': comment.content
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('add_project_comment', {
                'project_id': project_id,
                'comment_id': comment.id
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(comment.to_dict())
                
            flash('Comment added successfully', 'success')
            return redirect(url_for('projects.view_project', id=project_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding comment to project {project_id}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
            flash('Error adding comment', 'error')
            raise

    @bp.route('/tasks/<int:task_id>/comments/add', methods=['POST'])
    @login_required
    @requires_permission('projects_comment', 'write')
    @plugin_error_handler
    def add_task_comment(task_id):
        """Add a comment to a task."""
        try:
            task = Task.query.get_or_404(task_id)
            
            # Create comment
            comment = Comment(
                project_id=task.project_id,
                task_id=task_id,
                content=request.form['content'],
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(comment)
            
            # Add history entry
            history = History(
                entity_type='comment',
                project_id=task.project_id,
                task_id=task_id,
                action='created',
                details={
                    'content': comment.content
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.commit()
            
            plugin.log_action('add_task_comment', {
                'task_id': task_id,
                'comment_id': comment.id
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify(comment.to_dict())
                
            flash('Comment added successfully', 'success')
            return redirect(url_for('projects.view_task', id=task_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding comment to task {task_id}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
            flash('Error adding comment', 'error')
            raise

    @bp.route('/comments/<int:id>/edit', methods=['GET', 'POST'])
    @login_required
    @requires_permission('projects_comment', 'write')
    @plugin_error_handler
    def edit_comment(id):
        """Edit a comment."""
        try:
            comment = Comment.query.get_or_404(id)
            
            # Verify user can edit this comment
            if comment.user_id != current_user.id and not current_user.has_role('admin'):
                flash('You do not have permission to edit this comment', 'error')
                return redirect(url_for('projects.view_project', id=comment.project_id))
            
            if request.method == 'POST':
                old_content = comment.content
                comment.content = request.form['content']
                
                # Add history entry
                history = History(
                    entity_type='comment',
                    project_id=comment.project_id,
                    task_id=comment.task_id,
                    action='updated',
                    details={
                        'old_content': old_content,
                        'new_content': comment.content
                    },
                    created_by=current_user.username,
                    user_id=current_user.id
                )
                db.session.add(history)
                
                db.session.commit()
                
                plugin.log_action('edit_comment', {
                    'comment_id': comment.id
                })
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify(comment.to_dict())
                    
                flash('Comment updated successfully', 'success')
                if comment.task_id:
                    return redirect(url_for('projects.view_task', id=comment.task_id))
                return redirect(url_for('projects.view_project', id=comment.project_id))
                
            # GET request - show form
            return render_template('projects/comments/edit.html',
                                comment=comment)
                                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error editing comment {id}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
            flash('Error updating comment', 'error')
            raise

    @bp.route('/comments/<int:id>/delete', methods=['POST'])
    @login_required
    @requires_permission('projects_comment', 'write')
    @plugin_error_handler
    def delete_comment(id):
        """Delete a comment."""
        try:
            comment = Comment.query.get_or_404(id)
            
            # Verify user can delete this comment
            if comment.user_id != current_user.id and not current_user.has_role('admin'):
                flash('You do not have permission to delete this comment', 'error')
                return redirect(url_for('projects.view_project', id=comment.project_id))
            
            # Store IDs for redirect
            project_id = comment.project_id
            task_id = comment.task_id
            
            # Add history entry
            history = History(
                entity_type='comment',
                project_id=project_id,
                task_id=task_id,
                action='deleted',
                details={
                    'content': comment.content
                },
                created_by=current_user.username,
                user_id=current_user.id
            )
            db.session.add(history)
            
            db.session.delete(comment)
            db.session.commit()
            
            plugin.log_action('delete_comment', {
                'comment_id': id
            })
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'status': 'success'})
                
            flash('Comment deleted successfully', 'success')
            if task_id:
                return redirect(url_for('projects.view_task', id=task_id))
            return redirect(url_for('projects.view_project', id=project_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting comment {id}: {str(e)}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': str(e)}), 500
            flash('Error deleting comment', 'error')
            raise
