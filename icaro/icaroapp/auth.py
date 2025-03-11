from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session, g
)
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Roll
from flask_login import login_user, current_user
from icaroapp import db
import functools

bp = Blueprint('auth', __name__, url_prefix='/auth')


# Consultas SQL
def get_user(id):
    return User.query.get(id)  # Usa get() en lugar de filter_by().first()

# Antes de cada solicitud, si un usuario está conectado, se cargará en g.user
@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = User.query.get(user_id)  # Evita usar get_or_404()


# Vista de registro de usuarios
@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        roll_id = request.form.get('roll_id')

        error = None

        if not username or not email or not password:
            error = 'Todos los campos son obligatorios.'
        elif not roll_id:
            error = 'Debe seleccionar un rol.'
        elif User.query.filter_by(username=username).first():
            error = 'El nombre de usuario ya está en uso.'
        elif User.query.filter_by(email=email).first():
            error = 'El correo ya está registrado.'

        if error is None:
            user = User(username=username, email=email, password=generate_password_hash(password), roll_id=roll_id)
            db.session.add(user)
            db.session.commit()
            flash('Usuario creado correctamente')
            return redirect(url_for('admin.listusers'))

        flash(error)
        return redirect(url_for('auth.register'))

    roles = Roll.query.all()
    return render_template('auth/register.html', roles=roles)

@bp.route('/edituser/<int:id>', methods=('GET', 'POST'))
def edituser(id):
    user = get_user(id)

    if user is None:
        flash('El usuario no existe.')
        return redirect(url_for('admin.listusers'))

    roles = Roll.query.all()

    if request.method == 'POST':
        password = request.form.get('password')
        roll_id = request.form.get('roll_id')

        if password:
            user.password = generate_password_hash(password)  # Re-encriptar la nueva contraseña
        if roll_id:
            user.roll_id = roll_id

        db.session.commit()
        flash('Usuario editado correctamente')
        return redirect(url_for('admin.listusers'))

    return render_template('auth/edituser.html', roles=roles, user=user, user_rol=user.roll_id)

# Funciones de autenticación de usuarios
@bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['roll_id'] = user.roll_id
            flash('Usuario autenticado correctamente', 'success')
            return redirect(url_for('index'))  
        else:
            flash('Usuario o contraseña incorrectos', 'danger') 
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Decorador para requerir inicio de sesión
def login_required(view=None, allowed_roles=None):
    if view is None:
        return lambda v: login_required(v, allowed_roles)  # Permitir uso sin paréntesis

    if allowed_roles is None:
        allowed_roles = []

    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            flash('Debe iniciar sesión para acceder a esta página.')
            return redirect(url_for('auth.login'))

        if allowed_roles and g.user.roll_id not in allowed_roles:
            flash('No tiene permisos para acceder a esta página.', 'danger')
            return redirect(url_for('icaro.index'))

        return view(**kwargs)

    return wrapped_view