from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    dishes = db.relationship('Dish', secondary='order_dishes', backref=db.backref('orders', lazy='dynamic'))

order_dishes = db.Table('order_dishes',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id'), primary_key=True),
    db.Column('dish_id', db.Integer, db.ForeignKey('dish.id'), primary_key=True)
)
