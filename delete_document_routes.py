from app import db, create_app
from app.models import PageRouteMapping

def delete_document_routes():
    app = create_app()
    with app.app_context():
        PageRouteMapping.query.filter(PageRouteMapping.route.like('documents/%')).delete()
        db.session.commit()
        print("Successfully deleted document routes")

if __name__ == '__main__':
    delete_document_routes()
