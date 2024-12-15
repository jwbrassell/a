"""Routes for EC2 instance management."""
from flask import render_template, jsonify, request, current_app
from app.plugins.awsmon import bp
from app.plugins.awsmon.models import EC2Instance, AWSRegion, ChangeLog
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
import boto3
from datetime import datetime

def get_aws_session(region='us-east-1'):
    """Get boto3 session with credentials from Vault"""
    # TODO: Implement Vault credential retrieval
    return boto3.Session(region_name=region)

@bp.route('/')
@requires_permission('awsmon_dashboard_access')
def dashboard():
    """Main dashboard showing EC2 instances and their status"""
    regions = AWSRegion.query.all()
    instances = EC2Instance.query.all()
    return render_template(
        'awsmon/dashboard.html',
        regions=regions,
        instances=instances
    )

@bp.route('/instances')
@requires_permission('awsmon_instances_access')
def list_instances():
    """List all EC2 instances with their current status"""
    instances = EC2Instance.query.all()
    return render_template(
        'awsmon/instances.html',
        instances=instances
    )

@bp.route('/api/instances', methods=['GET'])
@requires_permission('awsmon_instances_access')
def api_list_instances():
    """API endpoint for instance data"""
    try:
        instances = EC2Instance.query.filter_by(deleted_at=None).all()
        return jsonify({
            'status': 'success',
            'data': [{
                'id': i.instance_id,
                'name': i.name,
                'type': i.instance_type,
                'state': i.state,
                'region': i.region.code,
                'public_ip': i.public_ip,
                'private_ip': i.private_ip,
                'is_jump_server': i.is_jump_server,
                'created_at': i.created_at.isoformat(),
                'updated_at': i.updated_at.isoformat() if i.updated_at else None,
                'created_by': i.created_by,
                'updated_by': i.updated_by
            } for i in instances]
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@bp.route('/api/instances/<instance_id>/action', methods=['POST'])
@requires_permission('awsmon_instances_access')
def instance_action(instance_id):
    """Control EC2 instance (start/stop/terminate)"""
    try:
        action = request.json.get('action')
        if action not in ['start', 'stop', 'terminate']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid action specified'
            }), 400

        instance = EC2Instance.query.filter_by(
            instance_id=instance_id,
            deleted_at=None
        ).first_or_404()
        
        session = get_aws_session(instance.region.code)
        ec2 = session.client('ec2')
        
        if action == 'start':
            ec2.start_instances(InstanceIds=[instance_id])
        elif action == 'stop':
            ec2.stop_instances(InstanceIds=[instance_id])
        elif action == 'terminate':
            ec2.terminate_instances(InstanceIds=[instance_id])
        
        # Log the change
        log = ChangeLog(
            action=action,
            resource_type='instance',
            resource_id=instance_id,
            details={'region': instance.region.code},
            user_id=current_app.config['current_user'].id
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': f'Instance {action} action initiated'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@bp.route('/api/poll')
@requires_permission('awsmon_instances_access')
def poll_instances():
    """Poll AWS API for instance updates"""
    try:
        for region in AWSRegion.query.all():
            session = get_aws_session(region.code)
            ec2 = session.client('ec2')
            
            # Get all instances in region
            response = ec2.describe_instances()
            instance_map = {}
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_map[instance['InstanceId']] = {
                        'state': instance['State']['Name'],
                        'public_ip': instance.get('PublicIpAddress'),
                        'private_ip': instance.get('PrivateIpAddress'),
                        'type': instance['InstanceType'],
                        'launch_time': instance['LaunchTime']
                    }
            
            # Update database
            current_user = current_app.config['current_user']
            for instance in EC2Instance.query.filter_by(
                region_id=region.id,
                deleted_at=None
            ):
                if instance.instance_id in instance_map:
                    data = instance_map[instance.instance_id]
                    instance.state = data['state']
                    instance.public_ip = data['public_ip']
                    instance.private_ip = data['private_ip']
                    instance.updated_at = datetime.utcnow()
                    instance.updated_by = current_user.id
            
            db.session.commit()
        
        return jsonify({
            'status': 'success',
            'message': 'Instance states updated successfully'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
