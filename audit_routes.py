from flask import current_app
from app import create_app
from app.extensions import db
from app.models import PageRouteMapping, NavigationCategory
from app.utils.route_manager import route_to_endpoint
import json
from collections import defaultdict
import inspect
import re

def get_view_info(view_func, endpoint, blueprint=None):
    """Extract template path and auth requirements from view function."""
    try:
        source = inspect.getsource(view_func)
    except (TypeError, OSError) as e:
        print(f"Warning: Could not get source for {endpoint}: {str(e)}")
        # Try to infer template from endpoint
        template_path = f"{endpoint.replace('.', '/')}.html"
        if blueprint:
            template_path = f"{blueprint}/templates/{template_path}"
        return {
            "renders_template": True,
            "template_path": template_path,
            "requires_auth": True,
            "required_permissions": []
        }
    
    info = {
        "renders_template": False,
        "template_path": None,
        "requires_auth": False,
        "required_permissions": []
    }
    
    # Check for template rendering - more inclusive patterns
    template_indicators = [
        'render_template',
        'template_name',
        'template',
        '.html',
        'jinja'
    ]
    
    for indicator in template_indicators:
        if indicator in source.lower():
            info["renders_template"] = True
            break
    
    # Try to extract template path
    if info["renders_template"]:
        # Look for common template patterns
        patterns = [
            r'render_template\([\'"]([^\'"]+)[\'"]',
            r'template_name\s*=\s*[\'"]([^\'"]+)[\'"]',
            r'template\s*=\s*[\'"]([^\'"]+)[\'"]'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, source)
            if match:
                info["template_path"] = match.group(1)
                break
                
        # If no template found but we think it renders one, use endpoint
        if not info["template_path"] and info["renders_template"]:
            info["template_path"] = f"{endpoint.replace('.', '/')}.html"
            if blueprint:
                info["template_path"] = f"{blueprint}/templates/{info['template_path']}"
    
    # Check for auth requirements - more inclusive
    auth_indicators = [
        '@login_required',
        'current_user.is_authenticated',
        'requires_auth',
        'auth_required',
        'check_auth',
        'check_authentication',
        '@requires_permission'
    ]
    
    for indicator in auth_indicators:
        if indicator in source:
            info["requires_auth"] = True
            break
    
    # Extract required permissions
    permission_matches = re.finditer(r'@requires_permission\([\'"]([^\'"]+)[\'"]', source)
    info["required_permissions"] = [m.group(1) for m in permission_matches]
            
    return info

def get_blueprint_name(endpoint):
    """Extract blueprint name from endpoint."""
    if '.' in endpoint:
        return endpoint.split('.')[0]
    return 'main'

def audit_routes():
    """Generate a comprehensive audit of all portal routes."""
    try:
        print("Creating Flask app...")
        app = create_app()
        
        print("Entering app context...")
        with app.app_context():
            print("\nScanning routes:")
            
            # Get all routes from Flask's URL map
            routes = []
            for rule in app.url_map.iter_rules():
                endpoint = rule.endpoint
                blueprint = get_blueprint_name(endpoint)
                
                # Skip technical endpoints
                if blueprint in ['static', 'debugtoolbar'] or endpoint.startswith('static'):
                    continue
                
                # Skip common API patterns
                if any(pattern in rule.rule.lower() for pattern in ['/api/', '/graphql', '/swagger']):
                    continue
                
                # Only include GET routes that might render pages
                if 'GET' not in rule.methods:
                    continue
                
                routes.append({
                    'endpoint': endpoint,
                    'route': rule.rule,
                    'blueprint': blueprint,
                    'methods': list(rule.methods - {'HEAD', 'OPTIONS'})
                })
                print(f"  • {rule.rule} ({endpoint})")
            
            print(f"\nFound {len(routes)} potential routes")
            
            # Get existing route mappings for additional info
            try:
                mapping_dict = {}
                for mapping in PageRouteMapping.query.all():
                    # Store both with and without trailing slash
                    route = mapping.route.rstrip('/')
                    mapping_dict[route] = mapping
                    mapping_dict[route + '/'] = mapping
            except Exception as e:
                print(f"Warning: Error querying route mappings: {str(e)}")
                mapping_dict = {}
            
            # Get categories for reference
            try:
                categories = {cat.id: cat.name for cat in NavigationCategory.query.all()}
            except Exception as e:
                print(f"Warning: Error querying categories: {str(e)}")
                categories = {}
            
            # Organize routes by blueprint (category)
            categorized_routes = defaultdict(list)
            
            print("\nAnalyzing routes:")
            for route_info in routes:
                endpoint = route_info['endpoint']
                print(f"\nChecking {endpoint}...")
                
                if endpoint in current_app.view_functions:
                    try:
                        view_func = current_app.view_functions[endpoint]
                        view_info = get_view_info(view_func, endpoint, route_info['blueprint'])
                        print(f"  Template: {view_info['template_path']}")
                        print(f"  Auth Required: {view_info['requires_auth']}")
                        if view_info['required_permissions']:
                            print(f"  Required Permissions: {', '.join(view_info['required_permissions'])}")
                    except Exception as e:
                        print(f"  Error analyzing view function: {str(e)}")
                        continue
                    
                    # Get additional info from mapping if available
                    mapping = mapping_dict.get(route_info['route'], None)
                    
                    # Include all GET routes that might render templates
                    if 'GET' in route_info['methods']:
                        route_data = {
                            "route": route_info['route'],
                            "page_name": mapping.page_name if mapping else endpoint.replace('.', ' ').title(),
                            "roles": [role.name for role in mapping.allowed_roles] if mapping else [],
                            "permissions": view_info['required_permissions'],
                            "endpoint": endpoint,
                            "weight": mapping.weight if mapping else 0,
                            "icon": mapping.icon if mapping else 'fa-link',
                            "shows_in_navbar": mapping.show_in_navbar if mapping else False,
                            "template": view_info["template_path"],
                            "requires_auth": view_info["requires_auth"],
                            "test_url": f"http://localhost:5000{route_info['route']}"
                        }
                        
                        if mapping and mapping.category_id in categories:
                            category_name = categories[mapping.category_id]
                        else:
                            category_name = route_info['blueprint'].replace('_', ' ').title()
                            
                        categorized_routes[category_name].append(route_data)
                        print("  ✓ Added to audit")
                    else:
                        print("  ✗ Skipped (not a GET route)")
                else:
                    print("  ✗ Skipped (no view function)")
            
            # Sort routes within each category by weight
            for category in categorized_routes:
                categorized_routes[category].sort(key=lambda x: x["weight"])
            
            # Generate the audit report
            audit_report = {
                "total_routes": sum(len(routes) for routes in categorized_routes.values()),
                "categories": dict(categorized_routes)
            }
            
            print("\nGenerating reports...")
            
            # Write JSON report
            try:
                with open('route_audit.json', 'w') as f:
                    json.dump(audit_report, f, indent=2)
                print("✓ JSON report written to route_audit.json")
            except Exception as e:
                print(f"Error writing JSON report: {str(e)}")
            
            # Generate HTML report
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Portal Route Audit</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .category {{ margin: 20px 0; }}
                    .route {{ margin: 10px 0 20px 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
                    .route h3 {{ margin: 0 0 10px 0; }}
                    .route p {{ margin: 5px 0; }}
                    .auth-required {{ color: #d63031; }}
                    .admin-required {{ color: #e17055; }}
                    .permission {{ display: inline-block; background: #00b894; color: white; padding: 2px 6px; border-radius: 3px; margin: 2px; }}
                    .test-link {{ display: inline-block; margin-top: 10px; padding: 5px 10px; background: #0984e3; color: white; text-decoration: none; border-radius: 4px; }}
                    .test-link:hover {{ background: #0769b5; }}
                </style>
            </head>
            <body>
                <h1>Portal Route Audit</h1>
                <p>Total Rendered Pages: {total_routes}</p>
            """.format(total_routes=audit_report['total_routes'])
            
            for category, routes in audit_report['categories'].items():
                html_content += f"""
                <div class="category">
                    <h2>{category} ({len(routes)} pages)</h2>
                """
                
                for route in routes:
                    auth_note = '<span class="auth-required">Requires Authentication</span>' if route['requires_auth'] else ''
                    admin_note = '<span class="admin-required">Admin Only</span>' if 'Administrator' in route['roles'] else ''
                    permissions = ''.join([f'<span class="permission">{p}</span>' for p in route['permissions']]) if route['permissions'] else ''
                    
                    html_content += f"""
                    <div class="route">
                        <h3>{route['page_name']} {auth_note} {admin_note}</h3>
                        <p><strong>URL:</strong> {route['route']}</p>
                        <p><strong>Template:</strong> {route['template']}</p>
                        <p><strong>Required Roles:</strong> {', '.join(route['roles']) if route['roles'] else 'No specific roles required'}</p>
                        <p><strong>Required Permissions:</strong> {permissions if permissions else 'No specific permissions required'}</p>
                        <p><strong>Shows in Navbar:</strong> {route['shows_in_navbar']}</p>
                        <a href="{route['test_url']}" target="_blank" class="test-link">Test Page</a>
                    </div>
                    """
                
                html_content += "</div>"
            
            html_content += """
            </body>
            </html>
            """
            
            # Write HTML report
            try:
                with open('route_audit.html', 'w') as f:
                    f.write(html_content)
                print("✓ HTML report written to route_audit.html")
                
                print("\nAudit reports generated successfully:")
                print("1. route_audit.json - Machine-readable format")
                print("2. route_audit.html - Interactive testing format")
                print("\nOpen route_audit.html in your browser to start testing the pages.")
            except Exception as e:
                print(f"Error writing HTML report: {str(e)}")
                
    except Exception as e:
        print(f"Error during route audit: {str(e)}")
        raise  # Re-raise the exception to see the full traceback

if __name__ == '__main__':
    audit_routes()
