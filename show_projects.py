from app import create_app
from app.plugins.projects.models import Project

app = create_app()

with app.app_context():
    projects = Project.query.all()
    print("\n=== Projects in Database ===")
    for project in projects:
        print(f"\nProject ID: {project.id}")
        print(f"Name: {project.name}")
        print(f"Summary: {project.summary}")
        print(f"Status: {project.status}")
        print(f"Priority: {project.priority}")
        print(f"Lead: {project.lead.username if project.lead else 'None'}")
        print(f"Created: {project.created_at}")
        print(f"Updated: {project.updated_at}")
        print("-" * 50)
