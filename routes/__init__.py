from flask import Blueprint

main_routes = Blueprint('main_routes', __name__)
auth_routes = Blueprint('auth_routes', __name__)
admin_routes = Blueprint('admin_routes', __name__)
courier_routes = Blueprint('courier_routes', __name__)

from .main_routes import *
from .auth_routes import *
from .admin_routes import *
from .courier_routes import *
