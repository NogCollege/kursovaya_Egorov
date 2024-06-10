from flask import render_template, Blueprint
from flask_login import login_required
from config import Config
import sqlite3
main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def index():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT name, price, category FROM products''')
        products = cursor.fetchall()
    return render_template('index.html', products=products)

@main_routes.route('/cart', methods=['GET'])
@login_required
def cart():
    return render_template('cart.html')
