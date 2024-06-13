import sqlite3
from config import Config
import time

def get_next_status(current_status):
    try:
        current_index = Config.STATUS_LIST.index(current_status)
        return Config.STATUS_LIST[min(current_index + 1, len(Config.STATUS_LIST) - 1)]
    except ValueError:
        return Config.STATUS_LIST[0]

def update_order_statuses():
    while True:
        with sqlite3.connect(Config.DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT id, status FROM test_orders')
            orders = cursor.fetchall()
            for order_id, current_status in orders:
                next_status = get_next_status(current_status)
                cursor.execute('UPDATE test_orders SET status = ? WHERE id = ?', (next_status, order_id))
            conn.commit()
        time.sleep(30) 
