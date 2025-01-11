
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from models import db, User, Post
from config import Config
from werkzeug.utils import secure_filename
import os
import re

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html', name='ФИО Студента', group='Группа', current_user=current_user)

@app.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html', name='ФИО Студента', group='Группа')

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html', name='ФИО Студента', group='Группа')

@app.route('/create_post', methods=['GET'])
@login_required
def create_post_page():
    return render_template('create_post.html', name='ФИО Студента', group='Группа')

@app.route('/edit_post/<int:post_id>', methods=['GET'])
@login_required
def edit_post_page(post_id):
    return render_template('edit_post.html', name='ФИО Студента', group='Группа', post_id=post_id)

@app.route('/admin', methods=['GET'])
@login_required
def admin_page():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    return render_template('admin.html', name='ФИО Студента', group='Группа')

@app.route('/api', methods=['POST'])
def api():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    method = data.get('method')
    params = data.get('params', {})
    id_ = data.get('id')
    if method == 'register':
        response = register(params)
    elif method == 'login':
        response = login(params)
    elif method == 'logout':
        response = logout()
    elif method == 'create_post':
        response = create_post(params)
    elif method == 'edit_post':
        response = edit_post(params)
    elif method == 'delete_post':
        response = delete_post(params)
    elif method == 'delete_account':
        response = delete_account()
    elif method == 'get_posts':
        response = get_posts()
    elif method == 'admin_delete_user':
        response = admin_delete_user(params)
    elif method == 'admin_delete_post':
        response = admin_delete_post(params)
    elif method == 'get_current_user':
        response = get_current_user()
    else:
        response = {'error': 'Method not found'}
    response['id'] = id_
    return jsonify(response)

def validate_login(login):
    return re.match("^[A-Za-z0-9_]+$", login)

def validate_password(password):
    return re.match("^[A-Za-z0-9@#$%^&+=!]+$", password)

def register(params):
    login = params.get('login')
    password = params.get('password')
    name = params.get('name')
    email = params.get('email')
    about = params.get('about', '')
    if not all([login, password, name, email]):
        return {'error': 'Missing required fields'}
    if not validate_login(login):
        return {'error': 'Invalid login'}
    if not validate_password(password):
        return {'error': 'Invalid password'}
    if User.query.filter_by(login=login).first():
        return {'error': 'Login already exists'}
    if User.query.filter_by(email=email).first():
        return {'error': 'Email already exists'}
    user = User(login=login, name=name, email=email, about=about)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return {'result': 'User registered successfully'}

def login(params):
    login_input = params.get('login')
    password = params.get('password')
    if not all([login_input, password]):
        return {'error': 'Missing login or password'}
    user = User.query.filter_by(login=login_input).first()
    if user and user.check_password(password):
        login_user(user)
        return {'result': 'Logged in successfully'}
    else:
        return {'error': 'Invalid credentials'}

def logout():
    logout_user()
    return {'result': 'Logged out successfully'}

def create_post(params):
    if not current_user.is_authenticated:
        return {'error': 'Authentication required'}
    topic = params.get('topic')
    content = params.get('content')
    if not all([topic, content]):
        return {'error': 'Missing topic or content'}
    post = Post(topic=topic, content=content, author=current_user)
    db.session.add(post)
    db.session.commit()
    return {'result': 'Post created successfully'}

def edit_post(params):
    if not current_user.is_authenticated:
        return {'error': 'Authentication required'}
    post_id = params.get('post_id')
    topic = params.get('topic')
    content = params.get('content')
    post = Post.query.get(post_id)
    if not post:
        return {'error': 'Post not found'}
    if post.author != current_user and not current_user.is_admin:
        return {'error': 'Permission denied'}
    if topic:
        post.topic = topic
    if content:
        post.content = content
    db.session.commit()
    return {'result': 'Post updated successfully'}

def delete_post(params):
    if not current_user.is_authenticated:
        return {'error': 'Authentication required'}
    post_id = params.get('post_id')
    post = Post.query.get(post_id)
    if not post:
        return {'error': 'Post not found'}
    if post.author != current_user and not current_user.is_admin:
        return {'error': 'Permission denied'}
    db.session.delete(post)
    db.session.commit()
    return {'result': 'Post deleted successfully'}

def delete_account():
    if not current_user.is_authenticated:
        return {'error': 'Authentication required'}
    user = current_user
    logout_user()
    posts = Post.query.filter_by(author=user).all()
    for post in posts:
        db.session.delete(post)
    db.session.delete(user)
    db.session.commit()
    return {'result': 'Account deleted successfully'}

def get_posts():
    posts = Post.query.all()
    result = []
    for post in posts:
        author = post.author
        post_data = {
            'id': post.id,
            'topic': post.topic,
            'content': post.content,
            'author': author.name,
            'user_id': author.id,
            'email': (author.email if (current_user.is_authenticated and (current_user.is_admin or author.id == current_user.id)) else None)
        }
        result.append(post_data)
    return {'result': result}

def admin_delete_user(params):
    if not current_user.is_authenticated or not current_user.is_admin:
        return {'error': 'Admin privileges required'}
    user_id = params.get('user_id')
    user = User.query.get(user_id)
    if not user:
        return {'error': 'User not found'}
    if user.is_admin:
        return {'error': 'Cannot delete admin user'}
    posts = Post.query.filter_by(author=user).all()
    for post in posts:
        db.session.delete(post)
    db.session.delete(user)
    db.session.commit()
    return {'result': 'User deleted successfully'}

def admin_delete_post(params):
    if not current_user.is_authenticated or not current_user.is_admin:
        return {'error': 'Admin privileges required'}
    post_id = params.get('post_id')
    post = Post.query.get(post_id)
    if not post:
        return {'error': 'Post not found'}
    db.session.delete(post)
    db.session.commit()
    return {'result': 'Post deleted successfully'}

def get_current_user():
    if current_user.is_authenticated:
        return {
            'result': {
                'is_authenticated': True,
                'is_admin': current_user.is_admin,
                'id': current_user.id
            }
        }
    else:
        return {
            'result': {
                'is_authenticated': False,
                'is_admin': False,
                'id': None
            }
        }

def initialize_database():
    db.create_all()
    if not User.query.filter_by(login='admin').first():
        admin = User(login='admin', name='Administrator', email='admin@example.com', is_admin=True)
        admin.set_password('adminpass')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        initialize_database()
    app.run(debug=True)
