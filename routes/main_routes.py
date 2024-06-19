from flask import render_template, Blueprint, request, session, redirect, url_for, flash
from flask_login import login_required
from config import Config
import sqlite3
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import random
import string

main_routes = Blueprint('main_routes', __name__)

def send_email(to_email, subject, message):
    smtp_server = 'smtp.mail.ru'
    smtp_port = 465
    smtp_user = 'mrsyrkus4@mail.ru'
    smtp_password = 'XW5JueT0bHFS0tfUa1B8'
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(message, 'plain'))
    
    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print("Сообщение отправлено успешно")
    except Exception as e:
        print(f"Сообщение не отправелено: {e}")

def get_cart_items():
    return session.get('cart', [])

def calculate_total(cart_items):
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    discount = session.get('discount', 0)
    if discount:
        total = total * (1 - discount / 100)
    return total


@main_routes.route('/')
def index():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT name, price, category, image FROM products''')
        products = cursor.fetchall()
        cursor.execute('''SELECT name, desc FROM sales''')
        sales = cursor.fetchall()
    return render_template('index.html', products=products, sales=sales)

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
            'product_type': product_type,
            'quantity': 1
        })
        session.modified = True
        return redirect(url_for('main_routes.index'))
    cart_items = session.get('cart', [])
    total = calculate_total(cart_items)
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


@main_routes.route('/view_order', methods=['POST', 'GET'])
@login_required
def order():
    cart_items = get_cart_items() 
    total = calculate_total(cart_items)
    return render_template('intouch.html', cart_items=cart_items, total=total)

def generate_order_number(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@main_routes.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart_items = session.get('cart', [])
    email = request.form['email']
    phone = request.form['phone']
    address = request.form['address']
    delivery = request.form['delivery_option']
    order_number = generate_order_number()
    status = "Готовится"

    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO test_orders (order_number, status) VALUES (?, ?)''',
                       (order_number, status))
        order_id = cursor.lastrowid
        for item in cart_items:
            cursor.execute('''INSERT INTO order_items (order_id, name, price, quantity) VALUES (?, ?, ?, ?)''',
                           (order_id, item['name'], item['price'], item['quantity']))
        conn.commit()

    message_for_admin = f"Новый заказ!\n\nНомер заказа: {order_number}\n\nНомер телефона: {phone}\n\nСпособ получения: {delivery}\n\nАдрес заказчика: {address}\n\nСписок товаров:\n"
    for item in cart_items:
        message_for_admin += f"- {item['name']} ({item['price']} руб.) x {item['quantity']}\n"
    message_for_admin += f"\nИтого: {sum(float(item['price']) * item['quantity'] for item in cart_items)} руб."

    message = f"Спасибо за ваш заказ!\n\nНомер заказа: {order_number}\n\nСписок товаров:\n"
    for item in cart_items:
        message += f"- {item['name']} ({item['price']} руб.) x {item['quantity']}\n"
    message += f"\nИтого: {sum(float(item['price']) * item['quantity'] for item in cart_items)} руб."

    send_email(email, "Ваш заказ принят", message)
    send_email(Config.ADMIN_EMAIL, "Новый заказ", message_for_admin)
    session.pop('cart', None)
    session.pop('discount', None)
    return redirect(url_for('main_routes.view_order', order_id=order_id))

@main_routes.route('/view_order/<int:order_id>')
@login_required
def view_order(order_id):
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''SELECT order_number, status FROM test_orders WHERE id = ?''', (order_id,))
        order = cursor.fetchone()
        cursor.execute('''SELECT name, price, quantity FROM order_items WHERE order_id = ?''', (order_id,))
        cart_items = cursor.fetchall()
    
    cart_items = [{'name': item[0], 'price': item[1], 'quantity': item[2]} for item in cart_items]
    total = sum(float(item['price']) * item['quantity'] for item in cart_items)
    return render_template('intouch.html', order_number=order[0], status=order[1], cart_items=cart_items, total=total)

@main_routes.route('/update_quantity/<item_name>', methods=['POST'])
@login_required
def update_quantity(item_name):
    new_quantity = int(request.form['quantity'])
    for item in session['cart']:
        if item['name'] == item_name:
            item['quantity'] = new_quantity
            break
    session.modified = True
    return redirect(url_for('main_routes.cart'))