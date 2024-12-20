"""
Security Group Routes
------------------
Routes for managing AWS security groups.
"""

from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration
from ..utils import get_aws_manager
from app.utils.enhanced_rbac import requires_permission

@aws_manager.route('/configurations/<int:config_id>/security-groups')
@requires_permission('aws_manage_security', 'read')
def list_security_groups(config_id):
    """List security groups for a configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    region = request.args.get('region')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON
        aws = get_aws_manager(config_id)
        groups = aws.get_security_groups(region)
        return jsonify(groups)
    else:
        # Regular request - return HTML
        return render_template('aws/security_groups.html', 
                            config=config,
                            active_page='security')

@aws_manager.route('/configurations/<int:config_id>/security-groups/<group_id>')
@requires_permission('aws_manage_security', 'read')
def get_security_group(config_id, group_id):
    """Get security group details"""
    region = request.args.get('region')
    if not region:
        abort(400, description="Region parameter is required")
    
    aws = get_aws_manager(config_id)
    try:
        groups = aws.get_security_groups(region)
        group = next((g for g in groups if g['group_id'] == group_id), None)
        if not group:
            abort(404, description="Security group not found")
        return jsonify(group)
    except Exception as e:
        current_app.logger.error(f"Failed to get security group details: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/security-groups', methods=['POST'])
@requires_permission('aws_manage_security', 'write')
def create_security_group(config_id):
    """Create a new security group"""
    data = request.get_json()
    required = ['name', 'description', 'vpc_id', 'region']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    aws = get_aws_manager(config_id)
    try:
        result = aws.create_security_group(
            region=data['region'],
            name=data['name'],
            description=data['description'],
            vpc_id=data['vpc_id']
        )
        return jsonify(result), 201
    except Exception as e:
        current_app.logger.error(f"Failed to create security group: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/security-groups/<group_id>', methods=['DELETE'])
@requires_permission('aws_manage_security', 'delete')
def delete_security_group(config_id, group_id):
    """Delete a security group"""
    region = request.args.get('region')
    if not region:
        abort(400, description="Region parameter is required")
    
    aws = get_aws_manager(config_id)
    try:
        aws.delete_security_group(region, group_id)
        return '', 204
    except Exception as e:
        current_app.logger.error(f"Failed to delete security group: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/security-groups/<group_id>/rules', methods=['POST'])
@requires_permission('aws_manage_security', 'write')
def add_security_group_rules(config_id, group_id):
    """Add rules to a security group"""
    data = request.get_json()
    required = ['rules', 'rule_type', 'region']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    if data['rule_type'] not in ['ingress', 'egress']:
        abort(400, description="Invalid rule type")
    
    aws = get_aws_manager(config_id)
    try:
        aws.add_security_group_rules(
            region=data['region'],
            group_id=group_id,
            rules=data['rules'],
            rule_type=data['rule_type']
        )
        return jsonify({'message': 'Rules added successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to add security group rules: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/security-groups/<group_id>/rules', methods=['DELETE'])
@requires_permission('aws_manage_security', 'delete')
def remove_security_group_rules(config_id, group_id):
    """Remove rules from a security group"""
    data = request.get_json()
    required = ['rules', 'rule_type', 'region']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    if data['rule_type'] not in ['ingress', 'egress']:
        abort(400, description="Invalid rule type")
    
    aws = get_aws_manager(config_id)
    try:
        aws.remove_security_group_rules(
            region=data['region'],
            group_id=group_id,
            rules=data['rules'],
            rule_type=data['rule_type']
        )
        return jsonify({'message': 'Rules removed successfully'})
    except Exception as e:
        current_app.logger.error(f"Failed to remove security group rules: {str(e)}")
        abort(500, description=str(e))
