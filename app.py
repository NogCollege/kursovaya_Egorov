from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import logging
import random
import string
import threading
import time

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = '36735ef9620b0bee5358d7e006c1f5b982c945314c10ed88'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


statuses = [
    "Готовится",
    "Готов, курьер спешит за ним",
    "Курьер забрал заказ и направляется к вам",
    "Заказ доставлен"
]

DATABASE = 'instance/database.db'

def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            username TEXT UNIQUE NOT NULL,
                            password TEXT NOT NULL,
                            is_admin TEXT NOT NULL,
                            is_courier TEXT NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            promocode TEXT NOT NULL,
                            discount INTEGER NOT NULL)''')

        cursor.execute('''CREATE TABLE IF NOT EXISTS sales (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            desc TEXT NOT NULL)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS test_orders (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            order_number TEXT NOT NULL,
                            status TEXT NOT NULL)''')

init_db()

class User(UserMixin):
    def __init__(self, id, username, password, is_admin, is_courier):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.is_courier = is_courier

    @staticmethod
    def get(user_id):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                return User(*user)
        return None

    @staticmethod
    def find_by_username(username):
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                return User(*user)
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (username, password, is_admin, is_courier) VALUES (?, ?, ?, ?)''', (username, hashed_password, "no", "no"))
                conn.commit()
            flash('Регистрация завершена. Теперь вы можете авторизоваться.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует', 'error')
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

def admin_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin == "yes":
            flash('У вас нет прав для просмотра данной страницы.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@login_manager.unauthorized_handler
def unauthorized_callback():
    flash('Для просмотра данной страницы вам нужно авторизоваться.', 'error')
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
@admin_required
def admin_panel():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT promocode, discount FROM orders')
        promo_codes = cursor.fetchall()
        cursor.execute('SELECT name, desc FROM sales')
        sales = cursor.fetchall()
    return render_template('panel.html', current_user=current_user, sales=sales, promo_codes=promo_codes, message=None)

@app.route('/change_admin_status', methods=['POST'])
@admin_required
def change_admin_status():
    username = request.form['username']
    action = request.form['action']
    new_status = 'yes' if action == 'grant' else 'no'
    with sqlite3.connect(DATABASE) as conn:
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

    return redirect(url_for('admin_panel'))

def courier_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_courier == "yes" or current_user.is_admin == "yes"):
            flash('У вас нет прав для просмотра данной страницы.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/courier', methods=['GET', 'POST'])
@courier_required
def courier_panel():
    if request.method == 'POST':
        order_id = request.form['order_id']
        new_status = request.form['status']
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE test_orders SET status = ? WHERE id = ?''', (new_status, order_id))
            conn.commit()
            flash('Статус заказа успешно обновлен.', 'success')
        return redirect(url_for('courier_panel')) 

    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, order_number, status FROM test_orders')
        orders = cursor.fetchall()
    
    return render_template('couriers.html', current_user=current_user, orders=orders)


@app.route('/change_courier_status', methods=['POST'])
@admin_required
def change_courier_status():
    courier_username = request.form['courier_username']
    courier_password = request.form['courier_password']
    hashed_password = generate_password_hash(courier_password, method='pbkdf2:sha256')
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO users (username, password, is_admin, is_courier) VALUES (?, ?, ?, ?)''', (courier_username, hashed_password, "no", "yes"))
        conn.commit()
        flash('Аккаунт для курьера успешно создан.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/cart', methods=['GET'])
@login_required
def cart():
    return render_template('cart.html')

@app.route('/create_delete_promocode', methods=['POST'])
@admin_required
def create_delete_promocode():
    promocode = request.form['promocode']
    discount = int(request.form['discount'])
    action = request.form['action2']
    with sqlite3.connect(DATABASE) as conn:
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
    return redirect(url_for('admin_panel'))

@app.route('/create_delete_sale', methods=['POST'])
@admin_required
def create_delete_sale():
    promotion = request.form['promotion_name']
    description = request.form['promotion_description']
    action = request.form['action3']
    with sqlite3.connect(DATABASE) as conn:
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
    return redirect(url_for('admin_panel'))

def generate_order_number():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

@app.route('/create_test_order', methods=['POST'])
@admin_required
def create_test_order():
    order_number = generate_order_number()
    status = "Готовится"
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''INSERT INTO test_orders (order_number, status) VALUES (?, ?)''', (order_number, status))
        conn.commit()
        flash(f'Тестовый заказ с номером {order_number} успешно создан.', 'success')
    return redirect(url_for('admin_panel'))


def update_order_statuses():
    while True:
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, status FROM test_orders')
            orders = cursor.fetchall()
            for order_id, current_status in orders:
                next_status = get_next_status(current_status)
                cursor.execute('UPDATE test_orders SET status = ? WHERE id = ?', (next_status, order_id))
            conn.commit()
        time.sleep(10) 

def get_next_status(current_status):
    try:
        current_index = statuses.index(current_status)
        return statuses[min(current_index + 1, len(statuses) - 1)]
    except ValueError:
        return statuses[0]

status_update_thread = threading.Thread(target=update_order_statuses, daemon=True)
status_update_thread.start()

if __name__ == '__main__':
    app.run(debug=True)
