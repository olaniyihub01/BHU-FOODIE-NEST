from flask import Flask, render_template_string, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_mysqldb import MySQL
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import yaml 

db = yaml.load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MSQL_USER'] =db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MSQL_DB'] = db['mysql_db']
mysql = MySQL(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True)

class MenuItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_item.id'), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    delivered = db.Column(db.Boolean, default=False)

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




# Routes
@app.route('/')
def index():
    return render_template_string(BASE_HTML + INDEX_HTML)

@app.route('/signUp.html', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!', 'success')
        return redirect(url_for('login.html'))
    return render_template_string(BASE_HTML + REGISTER_HTML)

@app.route('/login.html', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('restaurants'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template_string(BASE_HTML + LOGIN_HTML)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/restaurants')
@login_required
def restaurants():
    restaurants = Restaurant.query.all()
    return render_template_string(BASE_HTML + RESTAURANTS_HTML, restaurants=restaurants)

@app.route('/restaurant/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def restaurant_menu(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant.id).all()
    if request.method == 'POST':
        address = request.form['address']
        selected_items = request.form.getlist('menu_item')
        for item_id in selected_items:
            order = Order(user_id=current_user.id, restaurant_id=restaurant.id, menu_item_id=item_id, address=address)
            db.session.add(order)
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('order_confirmation', order_id=order.id))
    return render_template_string(BASE_HTML + RESTAURANT_MENU_HTML, restaurant=restaurant, menu_items=menu_items)

@app.route('/order/confirmation/<int:order_id>', methods=['GET', 'POST'])
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if request.method == 'POST':
        order.delivered = True
        db.session.commit()
        flash('Order confirmed as received!', 'success')
        return redirect(url_for('index'))
    return render_template_string(BASE_HTML + ORDER_CONFIRMATION_HTML, order=order)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)


