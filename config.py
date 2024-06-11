import os

class Config:
    SECRET_KEY = os.urandom(24)
    DATABASE = 'instance/database.db'
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    STATUS_LIST = [
        "Готовится",
        "Готов, курьер спешит за ним",
        "Курьер забрал заказ и направляется к вам",
        "Заказ доставлен"
    ]
