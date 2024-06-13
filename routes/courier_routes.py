from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import sqlite3
from config import Config
from routes import courier_routes

def courier_required(f):
    @login_required
    def decorated_function(*args, **kwargs):
        if not (current_user.is_courier == "yes" or current_user.is_admin == "yes"):
            flash('У вас нет прав для просмотра данной страницы.', 'error')
            return redirect(url_for('auth_routes.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@courier_routes.route('/courier', methods=['GET', 'POST'])
@courier_required
def courier_panel():
    if request.method == 'POST':
        order_id = request.form['order_id']
        new_status = request.form['status']
        with sqlite3.connect(Config.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('''UPDATE test_orders SET status = ? WHERE id = ?''', (new_status, order_id))
            conn.commit()
            flash('Статус заказа успешно обновлен.', 'success')
        return redirect(url_for('courier_routes.courier_panel')) 

    with sqlite3.connect(Config.DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT id, order_number, status FROM test_orders')
        orders = cursor.fetchall()
    
    return render_template('couriers.html', current_user=current_user, orders=orders)
