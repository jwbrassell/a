# Import all routes from the modular files
from . import connections
from . import reports
from . import queries

# The routes are automatically registered with the blueprint
# through the imports above, so no additional code is needed here.

# This file serves as a central point for importing all routes,
# making it easier to understand the structure of the blueprint.
