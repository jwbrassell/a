from flask import Blueprint

dispatch = Blueprint('dispatch', __name__, url_prefix='/dispatch',
                    template_folder='templates')

from . import routes
