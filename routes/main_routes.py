from flask import render_template, Blueprint, request, session, redirect, url_for, flash
from flask_login import login_required
from config import Config
import sqlite3

main_routes = Blueprint('main_routes', __name__)

@main_routes.route('/')
def index():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT name, price, category, image FROM products''')
        products = cursor.fetchall()
    return render_template('index.html', products=products)

@main_routes.route('/cart', methods=['GET', 'POST'])
@login_required
def cart():
    if request.method == 'POST':
        product_name = request.form.get('product_name')
        product_price = request.form.get('product_price')
        product_type = request.form.get('product_type')
        if 'cart' not in session:
            session['cart'] = []
        session['cart'].append({
            'name': product_name,
            'price': float(product_price),
            'product_type': product_type
        })
        session.modified = True
        return redirect(url_for('main_routes.cart'))
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)
    discount = session.get('discount', 0)
    if discount:
        total = total * (1 - discount / 100)
    return render_template('cart.html', cart_items=cart_items, total=total)

@main_routes.route('/clear_cart')
@login_required
def clear_cart():
    session.pop('cart', None)
    return redirect(url_for('main_routes.cart'))

@main_routes.route('/apply_promo', methods=['POST'])
def apply_promo():
    promo_code = request.form['promo_code']
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT discount FROM orders WHERE promocode = ?''', (promo_code,))
        promo = cursor.fetchone()
        if promo:
            session['discount'] = promo[0]
            flash(f'Промокод {promo_code} успешно применен', 'success')
        else:
            flash("Неверный промокод", "error")
    return redirect(url_for('main_routes.cart'))


@main_routes.route('/checkout', methods=['POST'])
@login_required
def checkout():
    return redirect(url_for('main_routes.index'))
