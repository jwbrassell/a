"""
IAM User Management Routes
-----------------------
Routes for managing AWS IAM users and their permissions.
"""

from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration
from ..utils import get_aws_manager
from app.utils.enhanced_rbac import requires_permission

@aws_manager.route('/configurations/<int:config_id>/iam')
@requires_permission('aws_manage_iam', 'read')
def list_iam_users(config_id):
    """List IAM users for a configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON
        aws = get_aws_manager(config_id)
        users = aws.get_iam_users()
        return jsonify(users)
    else:
        # Regular request - return HTML
        return render_template('aws/iam_users.html', 
                            config=config,
                            active_page='iam')

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/details')
@requires_permission('aws_manage_iam', 'read')
def get_iam_user_details(config_id, username):
    """Get detailed information about an IAM user"""
    aws = get_aws_manager(config_id)
    try:
        details = aws.get_iam_user_details(username)
        return jsonify(details)
    except Exception as e:
        current_app.logger.error(f"Failed to get IAM user details: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam', methods=['POST'])
@requires_permission('aws_manage_iam', 'write')
def create_iam_user(config_id):
    """Create a new IAM user"""
    data = request.get_json()
    required = ['username']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    aws = get_aws_manager(config_id)
    try:
        result = aws.create_iam_user(
            username=data['username'],
            create_access_key=data.get('create_access_key', True)
        )
        
        # If policies were provided, attach them
        if 'policies' in data:
            for policy_arn in data['policies']:
                aws.attach_user_policy(data['username'], policy_arn)
        
        # If groups were provided, add user to them
        if 'groups' in data:
            for group_name in data['groups']:
                aws.add_user_to_group(data['username'], group_name)
        
        return jsonify(result), 201
    except Exception as e:
        current_app.logger.error(f"Failed to create IAM user: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>', methods=['DELETE'])
@requires_permission('aws_manage_iam', 'delete')
def delete_iam_user(config_id, username):
    """Delete an IAM user"""
    aws = get_aws_manager(config_id)
    try:
        aws.delete_iam_user(username)
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Failed to delete IAM user: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/rotate-key', methods=['POST'])
@requires_permission('aws_manage_iam', 'update')
def rotate_iam_access_key(config_id, username):
    """Rotate access key for an IAM user"""
    aws = get_aws_manager(config_id)
    try:
        result = aws.rotate_access_key(username)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Failed to rotate access key: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/policies', methods=['POST'])
@requires_permission('aws_manage_iam', 'write')
def attach_user_policy(config_id, username):
    """Attach a policy to an IAM user"""
    data = request.get_json()
    if 'policy_arn' not in data:
        abort(400, description="Missing policy ARN")
    
    aws = get_aws_manager(config_id)
    try:
        aws.attach_user_policy(username, data['policy_arn'])
        return jsonify({'message': 'Policy attached successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to attach policy: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/policies/<path:policy_arn>', methods=['DELETE'])
@requires_permission('aws_manage_iam', 'delete')
def detach_user_policy(config_id, username, policy_arn):
    """Detach a policy from an IAM user"""
    aws = get_aws_manager(config_id)
    try:
        aws.detach_user_policy(username, policy_arn)
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Failed to detach policy: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/policies')
@requires_permission('aws_manage_iam', 'read')
def list_available_policies(config_id):
    """List available IAM policies"""
    aws = get_aws_manager(config_id)
    try:
        policies = aws.list_available_policies()
        return jsonify(policies)
    except Exception as e:
        current_app.logger.error(f"Failed to list policies: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/groups', methods=['POST'])
@requires_permission('aws_manage_iam', 'write')
def add_user_to_group(config_id, username):
    """Add an IAM user to a group"""
    data = request.get_json()
    if 'group_name' not in data:
        abort(400, description="Missing group name")
    
    aws = get_aws_manager(config_id)
    try:
        aws.add_user_to_group(username, data['group_name'])
        return jsonify({'message': 'User added to group successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to add user to group: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/<username>/groups/<group_name>', methods=['DELETE'])
@requires_permission('aws_manage_iam', 'delete')
def remove_user_from_group(config_id, username, group_name):
    """Remove an IAM user from a group"""
    aws = get_aws_manager(config_id)
    try:
        aws.remove_user_from_group(username, group_name)
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Failed to remove user from group: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/iam/groups')
@requires_permission('aws_manage_iam', 'read')
def list_iam_groups(config_id):
    """List IAM groups"""
    aws = get_aws_manager(config_id)
    try:
        groups = aws.list_iam_groups()
        return jsonify(groups)
    except Exception as e:
        current_app.logger.error(f"Failed to list groups: {str(e)}")
        abort(500, description=str(e))
