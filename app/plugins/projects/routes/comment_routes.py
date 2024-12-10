"""Comment management routes for the projects plugin."""

from flask import jsonify, request
from flask_login import login_required, current_user
from app.utils.rbac import requires_roles
from app.utils.activity_tracking import track_activity
from app.extensions import db
from app.models import UserActivity
from ..models import Project, Comment, History, Task
from app.plugins.projects import bp

@bp.route('/<int:project_id>/comments', methods=['GET'])
@login_required
@requires_roles('user')
def get_project_comments(project_id):
    """Get all comments for a project"""
    project = Project.query.get_or_404(project_id)
    return jsonify({
        'success': True,
        'comments': [comment.to_dict() for comment in project.comments]
    })

@bp.route('/<int:project_id>/comment', methods=['POST'])
@login_required
@requires_roles('user')
@track_activity
def create_comment(project_id):
    """Create a new comment for a project or task"""
    project = Project.query.get_or_404(project_id)
    data = request.get_json()
    
    # Check if this is a task comment
    task_id = data.get('task_id')
    if task_id:
        task = Task.query.get_or_404(task_id)
        if task.project_id != project_id:
            return jsonify({
                'success': False,
                'message': 'Task does not belong to this project'
            }), 400
    
    comment = Comment(
        content=data['content'],
        user_id=current_user.id,
        project_id=project_id,
        task_id=task_id
    )
    
    # Create history entry
    history = History(
        entity_type='comment',
        action='created',
        user_id=current_user.id,
        project_id=project.id,
        task_id=task_id,
        details={'content': data['content']}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Added comment to {'task in ' if task_id else ''}project: {project.name}"
    )
    
    db.session.add(comment)
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment added successfully',
        'comment': comment.to_dict()
    })

@bp.route('/comment/<int:comment_id>', methods=['GET'])
@login_required
@requires_roles('user')
def get_comment(comment_id):
    """Get a specific comment"""
    comment = Comment.query.get_or_404(comment_id)
    return jsonify({
        'success': True,
        'comment': comment.to_dict()
    })

@bp.route('/comment/<int:comment_id>', methods=['PUT'])
@login_required
@requires_roles('user')
@track_activity
def update_comment(comment_id):
    """Update a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Only allow the comment creator or admin to update
    if comment.user_id != current_user.id and not current_user.has_role('admin'):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to update this comment'
        }), 403
    
    data = request.get_json()
    old_content = comment.content
    comment.content = data['content']
    
    # Create history entry
    history = History(
        entity_type='comment',
        action='updated',
        user_id=current_user.id,
        project_id=comment.project_id,
        task_id=comment.task_id,
        details={
            'old_content': old_content,
            'new_content': comment.content
        }
    )
    comment.project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Updated comment in {'task in ' if comment.task_id else ''}project: {comment.project.name}"
    )
    
    db.session.add(activity)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment updated successfully',
        'comment': comment.to_dict()
    })

@bp.route('/comment/<int:comment_id>', methods=['DELETE'])
@login_required
@requires_roles('user')
@track_activity
def delete_comment(comment_id):
    """Delete a comment"""
    comment = Comment.query.get_or_404(comment_id)
    
    # Only allow the comment creator or admin to delete
    if comment.user_id != current_user.id and not current_user.has_role('admin'):
        return jsonify({
            'success': False,
            'message': 'Unauthorized to delete this comment'
        }), 403
    
    project = comment.project
    task_id = comment.task_id
    
    # Create history entry
    history = History(
        entity_type='comment',
        action='deleted',
        user_id=current_user.id,
        project_id=project.id,
        task_id=task_id,
        details={'content': comment.content}
    )
    project.history.append(history)
    
    # Log activity
    activity = UserActivity(
        user_id=current_user.id,
        username=current_user.username,
        activity=f"Deleted comment from {'task in ' if task_id else ''}project: {project.name}"
    )
    
    db.session.add(activity)
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Comment deleted successfully'
    })
