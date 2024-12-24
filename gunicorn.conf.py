import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Process naming
proc_name = 'portal'
default_proc_name = 'portal'

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Process management
preload_app = True
reload = False
reload_engine = 'auto'
spew = False
check_config = False

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    pass

def on_reload(server):
    """Called before code is reloaded."""
    pass

def when_ready(server):
    """Called just after the server is started."""
    pass

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    pass

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    # Flask-Session handles its own cleanup, so we don't need to do it here
    pass

def pre_exec(server):
    """Called just before a new master process is forked."""
    pass

def pre_request(worker, req):
    """Called just before a request."""
    worker.log.debug("%s %s" % (req.method, req.path))

def post_request(worker, req, environ, resp):
    """Called after a request."""
    pass

def worker_int(worker):
    """Called when a worker receives SIGINT or SIGTERM."""
    worker.log.info("worker received INT or TERM signal")

def worker_abort(worker):
    """Called when a worker receives SIGABRT."""
    worker.log.info("worker received ABORT signal")

def worker_exit(server, worker):
    """Called just after a worker has exited."""
    pass

def nworkers_changed(server, new_value, old_value):
    """Called after num_workers has been changed."""
    pass

# SSL config
keyfile = os.getenv('SSL_KEYFILE')
certfile = os.getenv('SSL_CERTFILE')

# Logging config
accesslog = os.getenv('GUNICORN_ACCESS_LOG', '-')
errorlog = os.getenv('GUNICORN_ERROR_LOG', '-')
loglevel = os.getenv('GUNICORN_LOG_LEVEL', 'info')

# Process naming
proc_name = os.getenv('GUNICORN_PROC_NAME', 'portal')

# Worker config
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = os.getenv('GUNICORN_WORKER_CLASS', 'sync')
worker_connections = int(os.getenv('GUNICORN_WORKER_CONNECTIONS', 1000))
timeout = int(os.getenv('GUNICORN_TIMEOUT', 120))
keepalive = int(os.getenv('GUNICORN_KEEPALIVE', 5))
max_requests = int(os.getenv('GUNICORN_MAX_REQUESTS', 1000))
max_requests_jitter = int(os.getenv('GUNICORN_MAX_REQUESTS_JITTER', 50))

# Server mechanics
daemon = os.getenv('GUNICORN_DAEMON', 'false').lower() == 'true'
raw_env = [
    f"FLASK_ENV={os.getenv('FLASK_ENV', 'production')}",
    f"FLASK_APP={os.getenv('FLASK_APP', 'wsgi.py')}"
]
