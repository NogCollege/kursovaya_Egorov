import os

class Config:
    SECRET_KEY = os.urandom(24)
    DATABASE = 'instance/database.db'
    STATUS_LIST = [
        "Готовится",
        "Готов, курьер спешит за ним",
        "Курьер забрал заказ и направляется к вам",
        "Заказ доставлен"
    ]
