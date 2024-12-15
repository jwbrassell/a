"""Routes for synthetic testing functionality."""
from flask import render_template, jsonify, request, current_app
from app.plugins.awsmon import bp
from app.plugins.awsmon.models import SyntheticTest, TestResult, EC2Instance
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
from datetime import datetime, timedelta

@bp.route('/synthetic')
@requires_permission('awsmon_synthetic_access')
def synthetic_tests():
    """Synthetic testing dashboard"""
    tests = SyntheticTest.query.filter_by(deleted_at=None).all()
    instances = EC2Instance.query.filter_by(deleted_at=None).all()
    return render_template(
        'awsmon/synthetic.html',
        tests=tests,
        instances=instances
    )

@bp.route('/api/synthetic/tests', methods=['GET', 'POST'])
@requires_permission('awsmon_synthetic_access')
def manage_tests():
    """Manage synthetic tests"""
    try:
        if request.method == 'POST':
            data = request.json
            current_user = current_app.config['current_user']
            
            # Validate required fields
            required_fields = ['name', 'type', 'target', 'instance_id']
            for field in required_fields:
                if field not in data:
                    return jsonify({
                        'status': 'error',
                        'message': f'Missing required field: {field}'
                    }), 400

            # Validate test type
            valid_types = ['ping', 'traceroute', 'port_check', 'http']
            if data['type'] not in valid_types:
                return jsonify({
                    'status': 'error',
                    'message': f'Invalid test type. Must be one of: {", ".join(valid_types)}'
                }), 400

            test = SyntheticTest(
                name=data['name'],
                test_type=data['type'],
                target=data['target'],
                frequency=data.get('frequency', 60),
                timeout=data.get('timeout', 5),
                instance_id=data['instance_id'],
                parameters=data.get('parameters', {}),
                created_by=current_user.id,
                updated_by=current_user.id
            )
            db.session.add(test)
            db.session.commit()
            
            return jsonify({
                'status': 'success',
                'message': 'Synthetic test created successfully',
                'data': {
                    'id': test.id,
                    'name': test.name,
                    'type': test.test_type,
                    'target': test.target,
                    'frequency': test.frequency,
                    'instance': test.instance.name,
                    'enabled': test.enabled,
                    'created_at': test.created_at.isoformat(),
                    'created_by': test.created_by
                }
            })
        
        # GET request - list all tests
        tests = SyntheticTest.query.filter_by(deleted_at=None).all()
        return jsonify({
            'status': 'success',
            'data': [{
                'id': t.id,
                'name': t.name,
                'type': t.test_type,
                'target': t.target,
                'frequency': t.frequency,
                'instance': t.instance.name,
                'enabled': t.enabled,
                'created_at': t.created_at.isoformat(),
                'updated_at': t.updated_at.isoformat() if t.updated_at else None,
                'created_by': t.created_by,
                'updated_by': t.updated_by
            } for t in tests]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@bp.route('/api/synthetic/tests/<int:test_id>', methods=['PUT', 'DELETE'])
@requires_permission('awsmon_synthetic_access')
def manage_test(test_id):
    """Update or delete a synthetic test"""
    try:
        test = SyntheticTest.query.filter_by(
            id=test_id,
            deleted_at=None
        ).first_or_404()
        current_user = current_app.config['current_user']

        if request.method == 'DELETE':
            test.deleted_at = datetime.utcnow()
            test.updated_by = current_user.id
            db.session.commit()
            return jsonify({
                'status': 'success',
                'message': 'Test deleted successfully'
            })

        # PUT request - update test
        data = request.json
        if 'name' in data:
            test.name = data['name']
        if 'type' in data:
            if data['type'] not in ['ping', 'traceroute', 'port_check', 'http']:
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid test type'
                }), 400
            test.test_type = data['type']
        if 'target' in data:
            test.target = data['target']
        if 'frequency' in data:
            test.frequency = data['frequency']
        if 'timeout' in data:
            test.timeout = data['timeout']
        if 'enabled' in data:
            test.enabled = data['enabled']
        if 'parameters' in data:
            test.parameters = data['parameters']
        
        test.updated_by = current_user.id
        test.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'status': 'success',
            'message': 'Test updated successfully',
            'data': {
                'id': test.id,
                'name': test.name,
                'type': test.test_type,
                'target': test.target,
                'frequency': test.frequency,
                'instance': test.instance.name,
                'enabled': test.enabled,
                'updated_at': test.updated_at.isoformat(),
                'updated_by': test.updated_by
            }
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@bp.route('/api/synthetic/results')
@requires_permission('awsmon_synthetic_access')
def test_results():
    """Get synthetic test results"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        results = TestResult.query\
            .join(SyntheticTest)\
            .filter(
                TestResult.created_at >= since,
                SyntheticTest.deleted_at == None
            )\
            .order_by(TestResult.created_at.desc())\
            .all()
        
        return jsonify({
            'status': 'success',
            'data': [{
                'test_id': r.test_id,
                'instance_id': r.instance_id,
                'status': r.status,
                'response_time': r.response_time,
                'error': r.error_message,
                'details': r.details,
                'timestamp': r.created_at.isoformat(),
                'created_by': r.created_by
            } for r in results]
        })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
