from app import create_app
import os
import multiprocessing

# Determine environment
env = os.getenv('FLASK_ENV', 'development')
app = create_app(env)

# Gunicorn configuration
workers = multiprocessing.cpu_count() * 2 + 1  # Number of worker processes
threads = 2  # Number of threads per worker
timeout = 120  # Worker timeout in seconds
keepalive = 5  # Keepalive timeout in seconds
max_requests = 1000  # Max requests per worker before restart
max_requests_jitter = 50  # Add randomness to max_requests
worker_class = 'sync'  # Worker class (sync, gevent, etc.)
worker_connections = 1000  # Maximum number of simultaneous connections

# Configure Gunicorn logging
accesslog = '-'  # Log to stdout
errorlog = '-'  # Log to stderr
loglevel = 'info'

if __name__ == "__main__":
    # Only run the development server when running directly
    if env == 'development':
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        # In production, use:
        # gunicorn -c wsgi.py wsgi:app
        pass
