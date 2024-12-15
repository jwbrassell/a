#!/usr/bin/env python3
"""
Script to verify plugin routes and permissions.
This script will:
1. Check all plugin routes are registered
2. Verify route permissions
3. Test route accessibility
4. Generate a routes report
"""
import os
import sys
import json
import logging
import importlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set
from flask import Flask

# Add project root to Python path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PluginRoutesVerifier:
    """Verify plugin routes and permissions."""
    
    def __init__(self):
        self.plugins_dir = Path('app/plugins')
        self.results = {
            'plugins': {},
            'unregistered_routes': [],
            'permission_issues': [],
            'accessibility_issues': []
        }
        
        # Create test Flask app
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
    def get_plugin_routes(self, plugin_dir: Path) -> List[Dict]:
        """Get all routes defined in a plugin."""
        routes = []
        
        try:
            # Look for route files
            route_files = list(plugin_dir.glob('*routes.py'))
            route_files.extend(plugin_dir.glob('*/*routes.py'))
            
            for route_file in route_files:
                # Import route module
                module_path = str(route_file.relative_to(project_root)).replace('/', '.')[:-3]
                module = importlib.import_module(module_path)
                
                # Look for route decorators
                for item_name in dir(module):
                    item = getattr(module, item_name)
                    if hasattr(item, '_endpoint'):
                        route_info = {
                            'endpoint': item._endpoint,
                            'methods': getattr(item, '_methods', ['GET']),
                            'url': getattr(item, '_rule', ''),
                            'permissions': getattr(item, '_permissions', []),
                            'module': module_path
                        }
                        routes.append(route_info)
        
        except Exception as e:
            logger.error(f"Failed to get routes from {plugin_dir}: {e}")
        
        return routes
        
    def verify_route_permissions(self, plugin_name: str, routes: List[Dict]):
        """Verify permissions for routes."""
        from app.utils.enhanced_rbac import get_permission
        
        permission_issues = []
        
        for route in routes:
            for permission in route['permissions']:
                # Check permission exists
                perm = get_permission(permission)
                if not perm:
                    issue = {
                        'route': route['endpoint'],
                        'permission': permission,
                        'issue': 'Permission does not exist'
                    }
                    permission_issues.append(issue)
                    
                # Check permission is registered to roles
                roles = perm.roles if perm else []
                if not roles:
                    issue = {
                        'route': route['endpoint'],
                        'permission': permission,
                        'issue': 'Permission not assigned to any roles'
                    }
                    permission_issues.append(issue)
        
        return permission_issues
        
    def verify_route_accessibility(self, plugin_name: str, routes: List[Dict]):
        """Verify routes are accessible."""
        accessibility_issues = []
        
        with self.app.test_client() as client:
            for route in routes:
                try:
                    # Try accessing route
                    response = client.get(route['url'])
                    
                    # Check response
                    if response.status_code not in [200, 302, 401, 403]:
                        issue = {
                            'route': route['endpoint'],
                            'status_code': response.status_code,
                            'issue': 'Unexpected status code'
                        }
                        accessibility_issues.append(issue)
                        
                except Exception as e:
                    issue = {
                        'route': route['endpoint'],
                        'issue': f'Failed to access: {str(e)}'
                    }
                    accessibility_issues.append(issue)
        
        return accessibility_issues
        
    def verify_plugin_routes(self):
        """Verify routes for all plugins."""
        for plugin_dir in self.plugins_dir.iterdir():
            if not plugin_dir.is_dir() or plugin_dir.name.startswith('__'):
                continue
                
            plugin_name = plugin_dir.name
            
            # Get plugin routes
            routes = self.get_plugin_routes(plugin_dir)
            
            # Verify route registration
            registered_routes = set()
            for rule in self.app.url_map.iter_rules():
                if rule.endpoint.startswith(f'{plugin_name}.'):
                    registered_routes.add(rule.endpoint)
            
            unregistered = []
            for route in routes:
                if route['endpoint'] not in registered_routes:
                    unregistered.append(route['endpoint'])
                    if route['endpoint'] not in self.results['unregistered_routes']:
                        self.results['unregistered_routes'].append(route['endpoint'])
            
            # Verify permissions
            permission_issues = self.verify_route_permissions(plugin_name, routes)
            self.results['permission_issues'].extend(permission_issues)
            
            # Verify accessibility
            accessibility_issues = self.verify_route_accessibility(plugin_name, routes)
            self.results['accessibility_issues'].extend(accessibility_issues)
            
            # Store plugin results
            self.results['plugins'][plugin_name] = {
                'routes': routes,
                'unregistered_routes': unregistered,
                'permission_issues': permission_issues,
                'accessibility_issues': accessibility_issues
            }
            
    def generate_report(self):
        """Generate a detailed routes report."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_plugins': len(self.results['plugins']),
                'total_routes': sum(
                    len(p['routes']) for p in self.results['plugins'].values()
                ),
                'unregistered_routes': len(self.results['unregistered_routes']),
                'permission_issues': len(self.results['permission_issues']),
                'accessibility_issues': len(self.results['accessibility_issues'])
            },
            'details': self.results
        }
        
        # Save report
        os.makedirs('routes_reports', exist_ok=True)
        report_path = os.path.join(
            'routes_reports',
            f'routes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        )
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        return report_path
        
    def print_summary(self, report_path: str):
        """Print summary of routes verification."""
        logger.info("\nRoutes Verification Summary:")
        logger.info("-" * 40)
        
        if self.results['unregistered_routes']:
            logger.warning("\nUnregistered routes:")
            for route in self.results['unregistered_routes']:
                logger.warning(f"- {route}")
        
        if self.results['permission_issues']:
            logger.warning("\nPermission issues:")
            for issue in self.results['permission_issues']:
                logger.warning(
                    f"- {issue['route']}: {issue['permission']} - {issue['issue']}"
                )
        
        if self.results['accessibility_issues']:
            logger.warning("\nAccessibility issues:")
            for issue in self.results['accessibility_issues']:
                logger.warning(f"- {issue['route']}: {issue['issue']}")
        
        logger.info(f"\nDetailed report saved to: {report_path}")
        
    def verify_routes(self):
        """Run complete routes verification."""
        try:
            self.verify_plugin_routes()
            report_path = self.generate_report()
            self.print_summary(report_path)
            
            # Return success if no issues found
            return not (
                self.results['unregistered_routes'] or
                self.results['permission_issues'] or
                self.results['accessibility_issues']
            )
            
        except Exception as e:
            logger.error(f"Routes verification failed: {e}")
            return False

def main():
    """Verify plugin routes."""
    verifier = PluginRoutesVerifier()
    success = verifier.verify_routes()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
