"""
AWS Configuration Routes
----------------------
Routes for managing AWS configurations and credentials.
"""

from flask import jsonify, request, render_template, current_app, abort
from .. import aws_manager
from ..models import AWSConfiguration
from ..constants import AWS_REGIONS
from app.extensions import db
from vault_utility import VaultUtility
from app.utils.enhanced_rbac import requires_permission

@aws_manager.route('/')
@requires_permission('aws_access', 'read')
def index():
    """AWS Manager Dashboard"""
    configs = AWSConfiguration.query.filter_by(is_active=True).all()
    return render_template('aws/configurations.html', 
                         configurations=configs, 
                         aws_regions=AWS_REGIONS,
                         active_page='configurations')

@aws_manager.route('/configurations')
@requires_permission('aws_access', 'read')
def list_configurations():
    """List all AWS configurations"""
    configs = AWSConfiguration.query.filter_by(is_active=True).all()
    return render_template('aws/configurations.html', 
                         configurations=configs, 
                         aws_regions=AWS_REGIONS,
                         active_page='configurations')

@aws_manager.route('/configurations', methods=['POST'])
@requires_permission('aws_manage_configurations', 'write')
def create_configuration():
    """Create a new AWS configuration"""
    data = request.get_json()
    
    # Validate required fields
    required = ['name', 'regions', 'access_key', 'secret_key']
    if not all(field in data for field in required):
        abort(400, description="Missing required fields")
    
    # Create vault path and store credentials
    vault_path = f"aws/{data['name']}"
    vault = VaultUtility()
    
    try:
        # Store credentials in vault
        vault.store_secret(vault_path, {
            'access_key': data['access_key'],
            'secret_key': data['secret_key']
        })
        
        # Create configuration record
        config = AWSConfiguration(
            name=data['name'],
            regions=data['regions'],
            vault_path=vault_path
        )
        db.session.add(config)
        db.session.commit()
        
        return jsonify({
            'id': config.id,
            'name': config.name,
            'regions': config.regions,
            'created_at': config.created_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        # Clean up vault entry if database commit fails
        try:
            vault.delete_secret(vault_path)
        except:
            pass
        current_app.logger.error(f"Failed to create AWS configuration: {str(e)}")
        abort(500, description="Failed to create configuration")

@aws_manager.route('/configurations/<int:config_id>', methods=['DELETE'])
@requires_permission('aws_manage_configurations', 'delete')
def delete_configuration(config_id):
    """Delete an AWS configuration"""
    config = AWSConfiguration.query.get_or_404(config_id)
    vault = VaultUtility()
    
    try:
        # Delete credentials from vault
        vault.delete_secret(config.vault_path)
        
        # Delete configuration from database
        db.session.delete(config)
        db.session.commit()
        
        return '', 204
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to delete AWS configuration: {str(e)}")
        abort(500, description="Failed to delete configuration")
