from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)  # En producción: usa hashing
    is_admin = db.Column(db.Boolean, default=False)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50))
    stock = db.Column(db.Integer, default=100)
    image = db.Column(db.String(200))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default='Pendiente', nullable=False)
    is_delivery = db.Column(db.Boolean, default=False)
    delivery_address = db.Column(db.Text)
    delivery_fee = db.Column(db.Float, default=5.0)

    order_items = db.relationship('OrderItem', backref='order', lazy=True, cascade="all, delete-orphan")

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# MODELO PARA CONFIGURACIÓN DEL SITIO (imagen de fondo del hero)
class SiteConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hero_image = db.Column(db.String(255), default='/static/images/default-hero.jpg')
    hero_title = db.Column(db.String(100), default='Restaurante Demo')
    hero_subtitle = db.Column(db.String(200), default='Comida deliciosa para cada estado de ánimo')