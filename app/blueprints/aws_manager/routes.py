"""
AWS Manager Routes
----------------
Main routes module for AWS Manager blueprint. Imports and exposes all route modules.
"""

# Import all route modules
from .routes.configurations import *
from .routes.health_events import *
from .routes.ec2 import *
from .routes.templates import *

# Routes will be available through the blueprint automatically
# due to the @aws_manager.route decorators in each module
