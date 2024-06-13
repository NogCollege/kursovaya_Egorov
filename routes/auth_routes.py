from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from models import User
from config import Config
import sqlite3
from routes import auth_routes


@auth_routes.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.find_by_username(username)
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main_routes.index'))
        else:
            flash('Неверное имя пользователя или пароль.', 'error')
    return render_template('login.html')

@auth_routes.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        try:
            with sqlite3.connect(Config.DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute('''INSERT INTO users (username, password, is_admin, is_courier) VALUES (?, ?, ?, ?)''', 
                               (username, hashed_password, "no", "no"))
                conn.commit()
                cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
                user_id = cursor.fetchone()[0]
                new_user = User(id=user_id, username=username, password=hashed_password, is_admin=False, is_courier=False)
                login_user(new_user)
                return redirect(url_for('main_routes.index'))
        except sqlite3.IntegrityError:
            flash('Пользователь с таким именем уже существует.', 'error')
            return redirect(url_for('auth_routes.register'))
    return render_template('register.html')


@auth_routes.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_routes.index'))
