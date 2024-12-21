from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration, EC2Template, EC2Instance
from ..utils import get_aws_manager
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission

@aws_manager.route('/configurations/<int:config_id>/ec2')
@requires_permission('aws_manage_ec2', 'read')
def list_ec2_instances(config_id):
    """List EC2 instances for a configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    region = request.args.get('region')
    next_token = request.args.get('next_token')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # AJAX request - return JSON
        aws = get_aws_manager(config_id)
        result = aws.get_ec2_instances(region, next_token)
        return jsonify({
            'instances': result['instances'],
            'next_token': result['next_token']
        })
    else:
        # Regular request - return HTML
        templates = EC2Template.query.filter_by(aws_config_id=config_id).all()
        return render_template('aws/ec2_instances.html', 
                            config=config, 
                            templates=templates,
                            active_page='ec2')

@aws_manager.route('/configurations/<int:config_id>/ec2/sync', methods=['POST'])
@requires_permission('aws_manage_ec2', 'write')
def sync_ec2_instances(config_id):
    """Sync EC2 instances with database"""
    aws = get_aws_manager(config_id)
    try:
        instances = aws.sync_ec2_instances(config_id)
        return jsonify({
            'message': 'Successfully synced EC2 instances',
            'instance_count': len(instances)
        })
    except Exception as e:
        current_app.logger.error(f"Failed to sync EC2 instances: {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/ec2/tracked')
@requires_permission('aws_manage_ec2', 'read')
def list_tracked_instances(config_id):
    """List tracked EC2 instances from database"""
    instances = EC2Instance.query.filter_by(aws_config_id=config_id).all()
    return jsonify([instance.to_dict() for instance in instances])

@aws_manager.route('/configurations/<int:config_id>/ec2', methods=['POST'])
@requires_permission('aws_manage_ec2', 'write')
def launch_ec2_instance(config_id):
    """Launch new EC2 instance(s)"""
    data = request.get_json()
    required = ['region', 'template_id']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    template = EC2Template.query.get_or_404(data['template_id'])
    if template.aws_config_id != config_id:
        abort(400, description="Template does not belong to this configuration")
    
    template_data = template.get_launch_config()
    
    aws = get_aws_manager(config_id)
    try:
        # Check if bulk launch
        count = data.get('count', 1)
        if count > 1:
            instances = aws.bulk_launch_ec2_instances(data['region'], template_data, count)
            return jsonify(instances), 201
        else:
            instance = aws.launch_ec2_instance(data['region'], template_data)
            return jsonify(instance), 201
    except Exception as e:
        current_app.logger.error(f"Failed to launch EC2 instance(s): {str(e)}")
        abort(500, description=str(e))

@aws_manager.route('/configurations/<int:config_id>/ec2/<instance_id>/<action>', methods=['POST'])
@requires_permission('aws_manage_ec2', 'update')
def control_ec2_instance(config_id, instance_id, action):
    """Control an EC2 instance (start, stop, terminate)"""
    if action not in ['start', 'stop', 'terminate']:
        abort(400, description="Invalid action")
    
    region = request.headers.get('X-AWS-Region')
    if not region:
        abort(400, description="Region header is required")
    
    aws = get_aws_manager(config_id)
    try:
        if action == 'start':
            result = aws.start_ec2_instance(instance_id, region)
        elif action == 'stop':
            result = aws.stop_ec2_instance(instance_id, region)
        else:  # terminate
            result = aws.terminate_ec2_instance(instance_id, region)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Failed to {action} EC2 instance: {str(e)}")
        abort(500, description=str(e))
