from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.utils import secure_filename

from models import db, User, MenuItem, Order, OrderItem, Expense, SiteConfig
from forms import LoginForm, MenuForm, OrderForm, ExpenseForm
from utils import generate_daily_report, generate_monthly_report
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Configuración de subida de archivos
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 8 * 1024 * 1024  # 8MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class FlaskUser(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.is_admin = user.is_admin

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return FlaskUser(user) if user else None

def init_db():
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='123456', is_admin=True)
            db.session.add(admin)
            db.session.commit()

init_db()

# Página principal
@app.route('/')
def index():
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
        db.session.commit()
    return render_template('index.html', config=config)

@app.route('/menu')
def menu():
    items = MenuItem.query.filter_by(is_active=True).all()
    return render_template('menu.html', items=items)

@app.route('/add_to_cart/<int:item_id>', methods=['POST'])
def add_to_cart(item_id):
    item = MenuItem.query.get_or_404(item_id)
    if not item.is_active:
        flash('Este producto no está disponible', 'warning')
        return redirect(url_for('menu'))
    
    if 'cart' not in session:
        session['cart'] = []
    
    for cart_item in session['cart']:
        if cart_item['id'] == item.id:
            cart_item['quantity'] += 1
            break
    else:
        session['cart'].append({'id': item.id, 'name': item.name, 'price': item.price, 'quantity': 1})
    
    session.modified = True
    flash(f'{item.name} agregado al carrito', 'success')
    return redirect(url_for('checkout'))

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart=cart_items, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    form = OrderForm()
    cart = session.get('cart', [])
    
    if not cart:
        flash('El carrito está vacío', 'warning')
        return redirect(url_for('menu'))
    
    if form.validate_on_submit():
        total = sum(item['price'] * item['quantity'] for item in cart)
        delivery_fee = 5.0 if form.is_delivery.data else 0.0
        total += delivery_fee
        
        payment_method = request.form.get('payment_method')
        
        order = Order(
            total=total,
            is_delivery=form.is_delivery.data,
            delivery_address=form.address.data if form.is_delivery.data else None,
            delivery_fee=delivery_fee,
            status='Pendiente'
        )
        db.session.add(order)
        db.session.commit()
        
        for item in cart:
            order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item['id'],
                quantity=item['quantity'],
                subtotal=item['price'] * item['quantity']
            )
            db.session.add(order_item)
        
        db.session.commit()
        session.pop('cart', None)
        
        if payment_method == 'efectivo':
            flash('¡Pedido confirmado! Pago en efectivo al recibir.', 'success')
        else:
            flash('¡Pedido confirmado! Realiza transferencia / Nequi / Daviplata al 3166683848 y envía comprobante.', 'success')
        
        return redirect(url_for('index'))
    
    subtotal = sum(item['price'] * item['quantity'] for item in cart)
    delivery_fee = 5.0 if form.is_delivery.data else 0
    total = subtotal + delivery_fee
    
    return render_template('order_form.html', form=form, subtotal=subtotal, delivery_fee=delivery_fee, total=total)

# Autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.password == form.password.data:
            login_user(FlaskUser(user))
            flash('Sesión iniciada', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Credenciales incorrectas', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sesión cerrada', 'info')
    return redirect(url_for('index'))

# Panel administrativo
@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    daily = generate_daily_report()
    monthly = generate_monthly_report()
    return render_template('admin_dashboard.html', daily=daily, monthly=monthly)

@app.route('/admin/menu', methods=['GET', 'POST'])
@login_required
def admin_menu():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    
    form = MenuForm()
    edit_id = request.args.get('edit', type=int)
    item_to_edit = MenuItem.query.get(edit_id) if edit_id else None
    
    if item_to_edit and request.method == 'GET':
        form.name.data = item_to_edit.name
        form.description.data = item_to_edit.description
        form.price.data = item_to_edit.price
        form.category.data = item_to_edit.category
        form.stock.data = item_to_edit.stock
    
    if form.validate_on_submit():
        item = item_to_edit if item_to_edit else MenuItem()
        item.name = form.name.data
        item.description = form.description.data
        item.price = form.price.data
        item.category = form.category.data
        item.stock = form.stock.data
        item.is_active = True
        
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                item.image = '/static/uploads/' + filename
        
        db.session.add(item)
        db.session.commit()
        flash('Producto guardado', 'success')
        return redirect(url_for('admin_menu'))
    
    items = MenuItem.query.all()
    return render_template('admin_menu.html', form=form, items=items, edit_id=edit_id, item_to_edit=item_to_edit)

@app.route('/admin/menu/deactivate/<int:item_id>', methods=['POST'])
@login_required
def deactivate_menu_item(item_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    item = MenuItem.query.get_or_404(item_id)
    item.is_active = False
    db.session.commit()
    flash(f'"{item.name}" desactivado', 'success')
    return redirect(url_for('admin_menu'))

@app.route('/admin/menu/reactivate/<int:item_id>', methods=['POST'])
@login_required
def reactivate_menu_item(item_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
    item = MenuItem.query.get_or_404(item_id)
    item.is_active = True
    db.session.commit()
    flash(f'"{item.name}" reactivado', 'success')
    return redirect(url_for('admin_menu'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))
    orders = Order.query.order_by(Order.date.desc()).all()
    return render_template('admin_orders.html', orders=orders)

@app.route('/admin/order/<int:order_id>/update_status', methods=['GET', 'POST'])
@login_required
def update_order_status(order_id):
    if not current_user.is_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))
    
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        new_status = request.form.get('status')
        valid_statuses = ['Pendiente', 'En preparación', 'Listo', 'Entregado', 'Cancelado']
        
        if new_status not in valid_statuses:
            flash('Estado inválido', 'danger')
            return redirect(url_for('update_order_status', order_id=order_id))
        
        old_status = order.status
        
        if old_status == 'Pendiente' and new_status in ['En preparación', 'Listo', 'Entregado']:
            for item in order.order_items:
                product = MenuItem.query.get(item.menu_item_id)
                if product.stock < item.quantity:
                    flash(f'Stock insuficiente para {product.name}', 'danger')
                    return redirect(url_for('update_order_status', order_id=order_id))
                product.stock -= item.quantity
                db.session.add(product)
        
        if old_status in ['En preparación', 'Listo', 'Entregado'] and new_status == 'Cancelado':
            for item in order.order_items:
                product = MenuItem.query.get(item.menu_item_id)
                product.stock += item.quantity
                db.session.add(product)
        
        order.status = new_status
        db.session.commit()
        
        flash(f'Estado actualizado a: {new_status}', 'success')
        return redirect(url_for('admin_orders'))
    
    return render_template('admin_update_status.html', order=order)

@app.route('/admin/accounting', methods=['GET', 'POST'])
@login_required
def admin_accounting():
    if not current_user.is_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))
    
    form = ExpenseForm()
    if form.validate_on_submit():
        expense = Expense(description=form.description.data, amount=form.amount.data)
        db.session.add(expense)
        db.session.commit()
        flash('Gasto registrado', 'success')
    
    expenses = Expense.query.order_by(Expense.date.desc()).all()
    return render_template('admin_accounting.html', form=form, expenses=expenses)

# RUTA PARA CAMBIAR IMAGEN DE FONDO DESDE ADMINISTRADOR
@app.route('/admin/site-config', methods=['GET', 'POST'])
@login_required
def admin_site_config():
    if not current_user.is_admin:
        flash('Acceso no autorizado', 'danger')
        return redirect(url_for('index'))
    
    config = SiteConfig.query.first()
    if not config:
        config = SiteConfig()
        db.session.add(config)
        db.session.commit()
    
    if request.method == 'POST':
        config.hero_title = request.form.get('hero_title', config.hero_title)
        config.hero_subtitle = request.form.get('hero_subtitle', config.hero_subtitle)
        
        if 'hero_image' in request.files:
            file = request.files['hero_image']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                config.hero_image = f'/static/uploads/{filename}'
        
        db.session.commit()
        flash('Imagen de fondo y configuración actualizadas correctamente', 'success')
        return redirect(url_for('admin_site_config'))
    
    return render_template('admin_site_config.html', config=config)

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)