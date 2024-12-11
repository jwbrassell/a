from app import create_app
from app.extensions import db
from app.models import PageRouteMapping, NavigationCategory, Role

app = create_app()
with app.app_context():
    # Get Tools category
    tools_category = NavigationCategory.query.filter_by(name='Tools').first()
    
    # Get user role
    user_role = Role.query.filter_by(name='user').first()
    admin_role = Role.query.filter_by(name='admin').first()
    
    # Create handoffs route mapping
    handoffs_route = PageRouteMapping(
        page_name='Handoffs',
        route='handoffs.index',
        icon='fa-exchange-alt',
        weight=320,  # After dispatch routes
        show_in_navbar=True,
        category_id=tools_category.id if tools_category else None
    )
    
    # Add roles
    if user_role:
        handoffs_route.allowed_roles.append(user_role)
    if admin_role:
        handoffs_route.allowed_roles.append(admin_role)
    
    # Add to database
    db.session.add(handoffs_route)
    db.session.commit()
    
    print("Added handoffs route mapping successfully")
