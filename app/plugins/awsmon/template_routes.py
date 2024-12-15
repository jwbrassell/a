"""Routes for jump server template management."""
from flask import render_template, jsonify, request, current_app
from app.plugins.awsmon.models import JumpServerTemplate
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission
from datetime import datetime

def register_routes(blueprint):
    """Register routes with the blueprint."""

    @blueprint.route('/templates')
    @requires_permission('awsmon_templates_access')
    def jump_server_templates():
        """Jump server template management"""
        templates = JumpServerTemplate.query.filter_by(deleted_at=None).all()
        return render_template(
            'awsmon/templates.html',
            templates=templates
        )

    @blueprint.route('/api/templates', methods=['GET', 'POST'])
    @requires_permission('awsmon_templates_access')
    def manage_templates():
        """Manage jump server templates"""
        try:
            if request.method == 'POST':
                data = request.json
                current_user = current_app.config['current_user']
                
                # Validate required fields
                required_fields = ['name', 'ami_id', 'instance_type']
                for field in required_fields:
                    if field not in data:
                        return jsonify({
                            'status': 'error',
                            'message': f'Missing required field: {field}'
                        }), 400

                template = JumpServerTemplate(
                    name=data['name'],
                    ami_id=data['ami_id'],
                    instance_type=data['instance_type'],
                    security_groups=data.get('security_groups', []),
                    user_data=data.get('user_data', ''),
                    created_by=current_user.id,
                    updated_by=current_user.id
                )
                db.session.add(template)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Jump server template created successfully',
                    'data': {
                        'id': template.id,
                        'name': template.name,
                        'ami_id': template.ami_id,
                        'instance_type': template.instance_type,
                        'created_at': template.created_at.isoformat(),
                        'created_by': template.created_by
                    }
                })
            
            # GET request - list all templates
            templates = JumpServerTemplate.query.filter_by(deleted_at=None).all()
            return jsonify({
                'status': 'success',
                'data': [{
                    'id': t.id,
                    'name': t.name,
                    'ami_id': t.ami_id,
                    'instance_type': t.instance_type,
                    'security_groups': t.security_groups,
                    'created_at': t.created_at.isoformat(),
                    'updated_at': t.updated_at.isoformat() if t.updated_at else None,
                    'created_by': t.created_by,
                    'updated_by': t.updated_by
                } for t in templates]
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400

    @blueprint.route('/api/templates/<int:template_id>', methods=['GET', 'PUT', 'DELETE'])
    @requires_permission('awsmon_templates_access')
    def manage_template(template_id):
        """Get, update or delete a jump server template"""
        try:
            template = JumpServerTemplate.query.filter_by(
                id=template_id,
                deleted_at=None
            ).first_or_404()
            current_user = current_app.config['current_user']

            if request.method == 'GET':
                return jsonify({
                    'status': 'success',
                    'data': {
                        'id': template.id,
                        'name': template.name,
                        'ami_id': template.ami_id,
                        'instance_type': template.instance_type,
                        'security_groups': template.security_groups,
                        'user_data': template.user_data,
                        'created_at': template.created_at.isoformat(),
                        'updated_at': template.updated_at.isoformat() if template.updated_at else None,
                        'created_by': template.created_by,
                        'updated_by': template.updated_by
                    }
                })

            elif request.method == 'DELETE':
                template.deleted_at = datetime.utcnow()
                template.updated_by = current_user.id
                db.session.commit()
                return jsonify({
                    'status': 'success',
                    'message': 'Template deleted successfully'
                })

            # PUT request - update template
            data = request.json
            if 'name' in data:
                template.name = data['name']
            if 'ami_id' in data:
                template.ami_id = data['ami_id']
            if 'instance_type' in data:
                template.instance_type = data['instance_type']
            if 'security_groups' in data:
                template.security_groups = data['security_groups']
            if 'user_data' in data:
                template.user_data = data['user_data']
            
            template.updated_by = current_user.id
            template.updated_at = datetime.utcnow()
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': 'Template updated successfully',
                'data': {
                    'id': template.id,
                    'name': template.name,
                    'ami_id': template.ami_id,
                    'instance_type': template.instance_type,
                    'security_groups': template.security_groups,
                    'updated_at': template.updated_at.isoformat(),
                    'updated_by': template.updated_by
                }
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400

    @blueprint.route('/api/templates/<int:template_id>/launch', methods=['POST'])
    @requires_permission('awsmon_templates_access')
    def launch_template(template_id):
        """Launch a new instance from a template"""
        try:
            template = JumpServerTemplate.query.filter_by(
                id=template_id,
                deleted_at=None
            ).first_or_404()
            current_user = current_app.config['current_user']

            # Additional launch parameters
            data = request.json or {}
            region_code = data.get('region', 'us-east-1')
            
            # TODO: Implement actual instance launch logic using boto3
            # This would involve:
            # 1. Getting AWS credentials from Vault
            # 2. Creating EC2 client for specified region
            # 3. Launching instance with template parameters
            # 4. Creating EC2Instance record in database
            
            return jsonify({
                'status': 'success',
                'message': 'Instance launch initiated',
                'data': {
                    'template_id': template.id,
                    'template_name': template.name,
                    'region': region_code
                }
            })

        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
