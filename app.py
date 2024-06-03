from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import logging

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = '36735ef9620b0bee5358d7e006c1f5b982c945314c10ed88'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

conn = sqlite3.connect('instance/database.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    is_admin TEXT NOT NULL)''')
conn.commit()
conn.close()

class User(UserMixin):
    def __init__(self, id, username, password, is_admin):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin

    @staticmethod
    def get(user_id):
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        conn.close()
        if user:
            return User(*user)
        return None

    @staticmethod
    def find_by_username(username):
        conn = sqlite3.connect('instance/database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        conn.close()
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
        logging.debug('Login form submitted.')
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)
        if user and check_password_hash(user.password, password):
            logging.debug('User authenticated successfully.')
            login_user(user)
            return redirect(url_for('index'))
        else:
            logging.debug('Authentication failed.')
            flash('Неправильное имя пользователя или пароль.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            conn = sqlite3.connect('instance/database.db')
            cursor = conn.cursor()
            cursor.execute('''INSERT INTO users (username, password, is_admin)
                              VALUES (?, ?, ?)''', (username, hashed_password, "no"))
            conn.commit()
            conn.close()

            flash('Регистрация прошла успешно. Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Имя пользователя уже существует.', 'error')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
