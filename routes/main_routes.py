from flask import render_template, Blueprint
from flask_login import login_required

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def index():
    return render_template('index.html')

@main_routes.route('/cart', methods=['GET'])
@login_required
def cart():
    return render_template('cart.html')
