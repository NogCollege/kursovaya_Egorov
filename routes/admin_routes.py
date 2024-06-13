from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import sqlite3
from config import Config
import random
import string
from routes import admin_routes
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin == "yes":
            flash('У вас нет прав для просмотра данной страницы.', 'error')
            return redirect(url_for('auth_routes.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_routes.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT promocode, discount FROM orders')
        promo_codes = cursor.fetchall()
        cursor.execute('SELECT name, desc FROM sales')
        sales = cursor.fetchall()
    return render_template('panel.html', current_user=current_user, sales=sales, promo_codes=promo_codes, message=None)

@admin_routes.route('/change_admin_status', methods=['POST'])
@admin_required
def change_admin_status():
    username = request.form['username']
    action = request.form['action']
    new_status = 'yes' if action == 'grant' else 'no'
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if not user:
            flash(f"Пользователь {username} не найден.", 'error')
        else:
            current_status = user[0]
            if current_status == 'yes' and action == 'grant':
                flash(f"Пользователь {username} уже имеет админ-статус.", 'error')
            else:
                cursor.execute('UPDATE users SET is_admin = ? WHERE username = ?', (new_status, username))
                conn.commit()
                action_text = 'выдан' if action == 'grant' else 'забрана'
                flash(f"Админ-панель {action_text} для пользователя {username}.", 'success')
    return redirect(url_for('admin_routes.admin_panel'))

@admin_routes.route('/create_delete_promocode', methods=['POST'])
@admin_required
def create_delete_promocode():
    promocode = request.form['promocode']
    discount = int(request.form['discount'])
    action = request.form['action2']
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        if action == 'create':
            cursor.execute('''INSERT INTO orders (promocode, discount) VALUES (?, ?)''', (promocode, discount))
            conn.commit()
            flash(f"Промокод {promocode} успешно создан.", 'success')
        else:
            cursor.execute('''DELETE FROM orders WHERE promocode = ? AND discount = ?''', (promocode, discount))
            conn.commit()
            if cursor.rowcount == 0:
                flash(f"Промокод {promocode} не найден.", 'error')
            else:
                flash(f"Промокод {promocode} успешно удален.", 'success')

    return redirect(url_for('admin_routes.admin_panel'))

@admin_routes.route('/create_product', methods=['POST'])
@admin_required
def create_product():
    name = request.form['product_name']
    price = request.form['product_price']
    category = request.form['category']  
    action = request.form['action4']
    file = request.files.get('product_image')
    filename = None

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        if action == 'create':
            cursor.execute('''INSERT INTO products (name, price, category, image) VALUES (?, ?, ?, ?)''', (name, price, category, filename))
            conn.commit()
            flash(f"Товар успешно добавлен.", 'success')
        else:
            cursor.execute('''DELETE FROM products WHERE name = ? AND price = ? AND category = ?''', (name, price, category))
            conn.commit()
            if cursor.rowcount == 0:
                flash(f"Данный товар не найден.", 'error')
            else:
                flash(f"Товар успешно удален", 'success')

        return redirect(url_for('admin_routes.admin_panel'))
    
@admin_routes.route('/create_delete_sale', methods=['POST'])
@admin_required
def create_delete_sale():
    promotion = request.form['promotion_name']
    description = request.form['promotion_description']
    action = request.form['action3']

    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor() 
        if action == 'create':
            cursor.execute('''INSERT INTO sales (name, desc) VALUES (?, ?)''', (promotion, description))
            conn.commit()
            flash("Акция успешно создана.", 'success')
        else:
            cursor.execute('''DELETE FROM sales WHERE name = ? AND desc = ?''', (promotion, description))
            conn.commit()
            if cursor.rowcount == 0:
                flash("Акция не найдена.", 'error')
            else:
                flash("Акция успешно удалена.", 'success')

    return redirect(url_for('admin_routes.admin_panel'))

@admin_routes.route('/change_courier_status', methods=['POST'])
@admin_required
def change_courier_status():
    courier_username = request.form['courier_username']
    courier_password = request.form['courier_password']
    hashed_password = generate_password_hash(courier_password, method='pbkdf2:sha256')

    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (username, password, is_admin, is_courier) VALUES (?, ?, ?, ?)''', (courier_username, hashed_password, "no", "yes"))
        conn.commit()
        flash('Аккаунт для курьера успешно создан.', 'success')

    return redirect(url_for('admin_routes.admin_panel'))

def generate_order_number(length=6):
    characters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

@admin_routes.route('/create_test_order', methods=['POST'])
@admin_required
def create_test_order():
    order_number = generate_order_number()
    status = "Готовится"
    
    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO test_orders (order_number, status) VALUES (?, ?)''', (order_number, status))
        conn.commit()
        flash(f'Тестовый заказ с номером {order_number} успешно создан.', 'success')

    return redirect(url_for('admin_routes.admin_panel'))
