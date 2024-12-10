from app import create_app

app = create_app()
with app.app_context():
    print("\nRegistered Flask Routes:")
    for rule in app.url_map.iter_rules():
        print(f"Endpoint: {rule.endpoint}, URL: {rule}")
