import os

class Config:
    SECRET_KEY = os.urandom(24)
    DATABASE = 'instance/database.db'
    UPLOAD_FOLDER = os.path.join('static', 'uploads')
    ADMIN_EMAIL = 'yasip@internet.ru'
    STATUS_LIST = [
        "Готовится",
        "Готов, курьер спешит за ним",
        "Курьер забрал заказ и направляется к вам",
        "Заказ доставлен"
    ]
