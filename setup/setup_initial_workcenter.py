from app import create_app
from app.extensions import db
from app.models.handoffs import WorkCenter, WorkCenterMember, HandoffSettings
from app.models.user import User
from app.models.role import Role

def setup_initial_workcenter():
    app = create_app()
    with app.app_context():
        # Get admin role
        admin_role = Role.query.filter_by(name='Administrator').first()
        if not admin_role:
            print("Administrator role not found")
            return

        # Get first user with admin role
        admin_user = User.query.join(User.roles).filter(Role.name == 'Administrator').first()
        if not admin_user:
            print("No user with Administrator role found")
            return

        # Create default workcenter if none exists
        if not WorkCenter.query.first():
            default_workcenter = WorkCenter(
                name="Default Team",
                description="Default team for handoffs"
            )
            db.session.add(default_workcenter)
            db.session.flush()  # Get the ID without committing

            # Add admin as workcenter admin
            member = WorkCenterMember(
                workcenter_id=default_workcenter.id,
                user_id=admin_user.id,
                is_admin=True
            )
            db.session.add(member)

            # Create default settings for the workcenter
            settings = HandoffSettings(
                workcenter_id=default_workcenter.id,
                priorities={
                    "Low": "info",
                    "Medium": "warning",
                    "High": "danger"
                },
                shifts=["Day Shift", "Night Shift"],
                require_close_comment=False,
                allow_close_with_comment=True
            )
            db.session.add(settings)

            db.session.commit()
            print(f"Created default workcenter with admin user: {admin_user.username}")
        else:
            print("Workcenter already exists")

if __name__ == '__main__':
    setup_initial_workcenter()
