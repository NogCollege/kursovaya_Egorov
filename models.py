import sqlite3
from flask_login import UserMixin
from config import Config

class User(UserMixin):
    def __init__(self, id, username, password, is_admin, is_courier):
        self.id = id
        self.username = username
        self.password = password
        self.is_admin = is_admin
        self.is_courier = is_courier

    @staticmethod
    def get(user_id):
        with sqlite3.connect(Config.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
            user = cursor.fetchone()
            if user:
                return User(*user)
        return None

    @staticmethod
    def find_by_username(username):
        with sqlite3.connect(Config.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
            user = cursor.fetchone()
            if user:
                return User(*user)
        return None

def init_db():
    with sqlite3.connect(Config.DATABASE) as conn:
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
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            name TEXT NOT NULL,
                            price TEXT NOT NULL,
                            category TEXT NOT NULL)''')

