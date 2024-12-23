from flask import Blueprint

handoffs = Blueprint('handoffs', __name__, url_prefix='/handoffs',
                    template_folder='templates')

from . import routes
