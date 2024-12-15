from flask import render_template, jsonify, request, current_app
from app.plugins.awsmon import bp
from app.plugins.awsmon.models import (
    EC2Instance, AWSRegion, SyntheticTest, TestResult,
    JumpServerTemplate, AWSCredential, ChangeLog
)
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
import boto3
from datetime import datetime, timedelta
import json

def get_aws_session(region='us-east-1'):
    """Get boto3 session with credentials from Vault"""
    # TODO: Implement Vault credential retrieval
    return boto3.Session(region_name=region)

@bp.route('/')
@requires_permission('awsmon_dashboard_access', 'read')
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
@requires_permission('awsmon_instances_access', 'read')
def list_instances():
    """List all EC2 instances with their current status"""
    instances = EC2Instance.query.all()
    return render_template(
        'awsmon/instances.html',
        instances=instances
    )

@bp.route('/api/instances', methods=['GET'])
@requires_permission('awsmon_instances_access', 'read')
def api_list_instances():
    """API endpoint for instance data"""
    instances = EC2Instance.query.all()
    return jsonify([{
        'id': i.instance_id,
        'name': i.name,
        'type': i.instance_type,
        'state': i.state,
        'region': i.region.code,
        'public_ip': i.public_ip,
        'private_ip': i.private_ip,
        'is_jump_server': i.is_jump_server
    } for i in instances])

@bp.route('/api/instances/<instance_id>/action', methods=['POST'])
@requires_permission('awsmon_instances_access', 'write')
def instance_action(instance_id):
    """Control EC2 instance (start/stop/terminate)"""
    action = request.json.get('action')
    instance = EC2Instance.query.filter_by(instance_id=instance_id).first_or_404()
    
    session = get_aws_session(instance.region.code)
    ec2 = session.client('ec2')
    
    try:
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
            details={'region': instance.region.code}
        )
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@bp.route('/synthetic')
@requires_permission('awsmon_synthetic_access', 'read')
def synthetic_tests():
    """Synthetic testing dashboard"""
    tests = SyntheticTest.query.all()
    instances = EC2Instance.query.all()
    return render_template(
        'awsmon/synthetic.html',
        tests=tests,
        instances=instances
    )

@bp.route('/api/synthetic/tests', methods=['GET', 'POST'])
@requires_permission('awsmon_synthetic_access', 'read', 'write')
def manage_tests():
    """Manage synthetic tests"""
    if request.method == 'POST':
        data = request.json
        test = SyntheticTest(
            name=data['name'],
            test_type=data['type'],
            target=data['target'],
            frequency=data.get('frequency', 60),
            timeout=data.get('timeout', 5),
            instance_id=data['instance_id'],
            parameters=data.get('parameters', {})
        )
        db.session.add(test)
        db.session.commit()
        return jsonify({'status': 'success', 'id': test.id})
    
    tests = SyntheticTest.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'type': t.test_type,
        'target': t.target,
        'frequency': t.frequency,
        'instance': t.instance.name,
        'enabled': t.enabled
    } for t in tests])

@bp.route('/api/synthetic/results')
@requires_permission('awsmon_synthetic_access', 'read')
def test_results():
    """Get synthetic test results"""
    hours = request.args.get('hours', 24, type=int)
    since = datetime.utcnow() - timedelta(hours=hours)
    
    results = TestResult.query\
        .filter(TestResult.created_at >= since)\
        .order_by(TestResult.created_at.desc())\
        .all()
    
    return jsonify([{
        'test_id': r.test_id,
        'instance_id': r.instance_id,
        'status': r.status,
        'response_time': r.response_time,
        'error': r.error_message,
        'details': r.details,
        'timestamp': r.created_at.isoformat()
    } for r in results])

@bp.route('/templates')
@requires_permission('awsmon_templates_access', 'read')
def jump_server_templates():
    """Jump server template management"""
    templates = JumpServerTemplate.query.all()
    return render_template(
        'awsmon/templates.html',
        templates=templates
    )

@bp.route('/api/templates', methods=['GET', 'POST'])
@requires_permission('awsmon_templates_access', 'read', 'write')
def manage_templates():
    """Manage jump server templates"""
    if request.method == 'POST':
        data = request.json
        template = JumpServerTemplate(
            name=data['name'],
            ami_id=data['ami_id'],
            instance_type=data['instance_type'],
            security_groups=data.get('security_groups', []),
            user_data=data.get('user_data', '')
        )
        db.session.add(template)
        db.session.commit()
        return jsonify({'status': 'success', 'id': template.id})
    
    templates = JumpServerTemplate.query.all()
    return jsonify([{
        'id': t.id,
        'name': t.name,
        'ami_id': t.ami_id,
        'instance_type': t.instance_type
    } for t in templates])

@bp.route('/settings')
@requires_permission('awsmon_settings_access', 'read')
def aws_settings():
    """AWS credentials and settings management"""
    credentials = AWSCredential.query.all()
    return render_template(
        'awsmon/settings.html',
        credentials=credentials
    )

@bp.route('/api/poll')
@requires_permission('awsmon_instances_access', 'read')
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
            for instance in EC2Instance.query.filter_by(region_id=region.id):
                if instance.instance_id in instance_map:
                    data = instance_map[instance.instance_id]
                    instance.state = data['state']
                    instance.public_ip = data['public_ip']
                    instance.private_ip = data['private_ip']
                    instance.updated_at = datetime.utcnow()
            
            db.session.commit()
        
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400
