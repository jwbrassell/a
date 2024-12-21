from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration, EC2Template
from app.extensions import db
from app.utils.enhanced_rbac import requires_permission

@aws_manager.route('/configurations/<int:config_id>/templates')
@requires_permission('aws_manage_templates', 'read')
def list_templates(config_id):
    """List EC2 templates for a configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    templates = EC2Template.query.filter_by(aws_config_id=config_id).all()
    return render_template('aws/templates.html', 
                         config=config, 
                         templates=templates,
                         active_page='templates')

@aws_manager.route('/configurations/<int:config_id>/templates/<int:template_id>')
@requires_permission('aws_manage_templates', 'read')
def get_template(config_id, template_id):
    """Get EC2 template details"""
    template = EC2Template.query.get_or_404(template_id)
    if template.aws_config_id != config_id:
        abort(404)
    
    return jsonify(template.to_dict())

@aws_manager.route('/configurations/<int:config_id>/templates', methods=['POST'])
@requires_permission('aws_manage_templates', 'write')
def create_template(config_id):
    """Create a new EC2 template"""
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'instance_type', 'ami_id']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    template = EC2Template(
        name=data['name'],
        description=data.get('description'),
        instance_type=data['instance_type'],
        ami_id=data['ami_id'],
        key_name=data.get('key_name'),
        security_groups=data.get('security_groups', []),
        user_data=data.get('user_data'),
        tags=data.get('tags', {}),
        aws_config_id=config_id
    )
    
    try:
        db.session.add(template)
        db.session.commit()
        return jsonify(template.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to create template: {str(e)}")
        abort(500, description="Failed to create template")

@aws_manager.route('/configurations/<int:config_id>/templates/<int:template_id>', methods=['PUT'])
@requires_permission('aws_manage_templates', 'write')
def update_template(config_id, template_id):
    """Update an EC2 template"""
    template = EC2Template.query.get_or_404(template_id)
    if template.aws_config_id != config_id:
        abort(404)
    
    data = request.get_json()
    
    # Update fields if provided
    if 'name' in data:
        template.name = data['name']
    if 'description' in data:
        template.description = data['description']
    if 'instance_type' in data:
        template.instance_type = data['instance_type']
    if 'ami_id' in data:
        template.ami_id = data['ami_id']
    if 'key_name' in data:
        template.key_name = data['key_name']
    if 'security_groups' in data:
        template.security_groups = data['security_groups']
    if 'user_data' in data:
        template.user_data = data['user_data']
    if 'tags' in data:
        template.tags = data['tags']
    
    try:
        db.session.commit()
        return jsonify(template.to_dict())
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to update template: {str(e)}")
        abort(500, description="Failed to update template")

@aws_manager.route('/configurations/<int:config_id>/templates/<int:template_id>', methods=['DELETE'])
@requires_permission('aws_manage_templates', 'delete')
def delete_template(config_id, template_id):
    """Delete an EC2 template"""
    template = EC2Template.query.get_or_404(template_id)
    if template.aws_config_id != config_id:
        abort(404)
    
    try:
        db.session.delete(template)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete template: {str(e)}")
        abort(500, description="Failed to delete template")
