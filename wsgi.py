import os
from app import create_app

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == "__main__":
    # Only run the development server when running directly
    if env == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # In production, use:
        # gunicorn -c gunicorn.conf.py wsgi:app
        pass
