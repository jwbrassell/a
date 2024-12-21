from flask import Blueprint, render_template, jsonify, request, current_app, g
from flask_login import login_required
from app.utils.vault_security_monitor import VaultSecurityMonitor
from app.utils.vault_policy_manager import VaultPolicyManager
from app.utils.vault_middleware import VaultPolicyEnforcer
from vault_utility import VaultUtility, VaultError
from datetime import datetime, timedelta
import json

# API Blueprint
vault_bp = Blueprint('vault', __name__, url_prefix='/api/vault')
# Dashboard Blueprint
vault_dashboard_bp = Blueprint('vault_dashboard', __name__, url_prefix='/admin/vault')

vault_monitor = VaultSecurityMonitor()
vault_util = VaultUtility()
policy_manager = VaultPolicyManager(vault_util)
policy_enforcer = VaultPolicyEnforcer(vault_util)

# Decorator for vault admin access
def requires_vault_admin(f):
    return policy_enforcer.requires_vault_permission(
        "sys/policies/*", 
        "update"
    )(f)

# Decorator for vault metrics access
def requires_vault_metrics_access(f):
    return policy_enforcer.requires_vault_permission(
        "sys/metrics/*", 
        "read"
    )(f)

# Dashboard Routes
@vault_dashboard_bp.route('/')
@login_required
@requires_vault_admin
def dashboard():
    """Display vault management dashboard."""
    try:
        context = {
            'vault_available': g.get('vault_available', False),
            'vault_error': g.get('vault_error', None)
        }
        
        if context['vault_available']:
            # Get security report
            context['report'] = vault_monitor.generate_security_report()
            
            # Get policies
            context['policies'] = policy_manager.list_policies()
            
            # Get LDAP status if configured
            try:
                ldap_config = vault_util.client.auth.ldap.read_configuration()
                context['ldap_configured'] = bool(ldap_config)
            except:
                context['ldap_configured'] = False
            
        return render_template('admin/vault_dashboard.html', **context)
    except Exception as e:
        current_app.logger.error(f"Failed to load vault dashboard: {e}")
        return render_template('admin/vault_dashboard.html', error=str(e))

@vault_dashboard_bp.route('/status')
@login_required
@requires_vault_admin
def status():
    """Display vault status page."""
    try:
        context = {
            'vault_available': g.get('vault_available', False),
            'vault_error': g.get('vault_error', None)
        }
        
        if context['vault_available']:
            context['report'] = vault_monitor.generate_security_report()
            
        return render_template('admin/vault_status.html', **context)
    except Exception as e:
        current_app.logger.error(f"Failed to load vault status: {e}")
        return render_template('admin/vault_status.html', error=str(e))

# API Routes
@vault_bp.route('/health')
@login_required
@requires_vault_admin
def vault_health():
    """Get vault health status."""
    try:
        if not g.vault_available:
            return jsonify({
                'status': 'unavailable',
                'error': g.vault_error
            }), 503
            
        report = vault_monitor.generate_security_report()
        
        # Add LDAP status
        try:
            ldap_config = vault_util.client.auth.ldap.read_configuration()
            report['ldap_status'] = {
                'configured': True,
                'url': ldap_config['data'].get('url'),
                'userdn': ldap_config['data'].get('userdn')
            }
        except:
            report['ldap_status'] = {'configured': False}
            
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/policies', methods=['GET'])
@login_required
@requires_vault_admin
def list_policies():
    """List all policies."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        policies = policy_manager.list_policies()
        
        # Get detailed info for each policy
        policy_details = []
        for policy_name in policies:
            try:
                details = policy_manager.get_policy_info(policy_name)
                policy_details.append(details)
            except:
                continue
                
        return jsonify(policy_details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/policies/<name>', methods=['GET'])
@login_required
@requires_vault_admin
def get_policy(name):
    """Get a specific policy."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        policy = policy_manager.get_policy_info(name)
        return jsonify(policy)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/policies', methods=['POST'])
@login_required
@requires_vault_admin
def create_policy():
    """Create a new policy."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        data = request.get_json()
        if not data or 'name' not in data or 'paths' not in data:
            return jsonify({'error': 'Invalid policy data'}), 400
            
        if data.get('type') == 'blueprint':
            success = policy_manager.create_blueprint_policy(
                data['name'],
                data['paths']
            )
        else:
            success = policy_manager.create_role_policy(
                data['name'],
                data['paths']
            )
            
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/policies/<name>', methods=['DELETE'])
@login_required
@requires_vault_admin
def delete_policy(name):
    """Delete a policy."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        success = policy_manager.delete_policy(name)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/ldap/config', methods=['POST'])
@login_required
@requires_vault_admin
def configure_ldap():
    """Configure LDAP authentication."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        data = request.get_json()
        required_fields = ['url', 'binddn', 'bindpass', 'userdn', 'groupdn']
        
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required LDAP configuration fields'}), 400
            
        success = policy_manager.setup_ldap_auth(data)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/ldap/groups', methods=['POST'])
@login_required
@requires_vault_admin
def map_ldap_group():
    """Map LDAP group to policies."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        data = request.get_json()
        if not data or 'group' not in data or 'policies' not in data:
            return jsonify({'error': 'Invalid group mapping data'}), 400
            
        success = policy_manager.map_ldap_group_to_policies(
            data['group'],
            data['policies']
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/secrets', methods=['GET'])
@login_required
def list_secrets():
    """List accessible secrets paths."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        # Use policy enforcer to filter accessible paths
        secrets = vault_util.list_secrets()
        accessible_secrets = []
        
        for secret_path in secrets:  # secrets is now a list of strings
            if policy_enforcer._check_path_permission(f"kvv2/data/{secret_path}", "read"):
                accessible_secrets.append({
                    'path': secret_path,
                    'readable': True
                })
                
        return jsonify(accessible_secrets)
    except VaultError as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/secrets/<path:secret_path>', methods=['GET'])
@login_required
@policy_enforcer.requires_vault_permission("kvv2/data/${path}", "read")
def get_secret(secret_path):
    """Get a specific secret."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        secret = vault_util.get_secret(secret_path)
        return jsonify(secret)
    except VaultError as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/secrets/<path:secret_path>', methods=['POST'])
@login_required
@policy_enforcer.requires_vault_permission("kvv2/data/${path}", "create")
def create_secret(secret_path):
    """Create a new secret."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        data = request.get_json()
        vault_util.store_secret(secret_path, data)  # Changed from create_secret to store_secret
        return jsonify({'message': 'Secret created successfully'})
    except VaultError as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/secrets/<path:secret_path>', methods=['PUT'])
@login_required
@policy_enforcer.requires_vault_permission("kvv2/data/${path}", "update")
def update_secret(secret_path):
    """Update an existing secret."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        data = request.get_json()
        vault_util.store_secret(secret_path, data)  # Using store_secret for consistency
        return jsonify({'message': 'Secret updated successfully'})
    except VaultError as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/secrets/<path:secret_path>', methods=['DELETE'])
@login_required
@policy_enforcer.requires_vault_permission("kvv2/data/${path}", "delete")
def delete_secret(secret_path):
    """Delete a secret."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
        vault_util.delete_secret(secret_path)
        return jsonify({'message': 'Secret deleted successfully'})
    except VaultError as e:
        return jsonify({'error': str(e)}), 500

@vault_bp.route('/metrics')
@login_required
@requires_vault_metrics_access
def get_metrics():
    """Get vault metrics for graphing."""
    try:
        if not g.vault_available:
            return jsonify({'error': 'Vault unavailable'}), 503
            
        # Get metrics from the last 24 hours
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        # Get actual metrics if available, otherwise use mock data
        try:
            metrics = vault_util.get_metrics(start_time, end_time)
        except:
            # Generate mock data points every 5 minutes
            metrics = []
            current_time = start_time
            while current_time <= end_time:
                metrics.append({
                    'timestamp': current_time.isoformat(),
                    'response_time': 100,  # Mock response time in ms
                    'active_tokens': 50,   # Mock number of active tokens
                    'requests_per_second': 20  # Mock requests/second
                })
                current_time += timedelta(minutes=5)

        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
