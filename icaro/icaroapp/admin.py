from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, session
)
from .models import Roll, User
from icaroapp import db 
from icaroapp.auth import login_required

bp = Blueprint('admin', __name__, url_prefix='/admin')

# Consultas SQL
def get_rol(id):
    return Roll.query.filter_by(id=id).first()

def get_user(id):
    return User.query.filter_by(id=id).first()


# Vistas de administrador 

@bp.route('/crearol', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def crearol():
    if request.method == 'POST':
        rolname = request.form.get('rolname')
        roldesc = request.form.get('roldescription')

        if not rolname or not roldesc:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('admin.crearol'))

        rol_existente = Roll.query.filter_by(roll_name=rolname).first()

        if rol_existente is None:
            nuevo_rol = Roll(roll_name=rolname, roll_description=roldesc)
            db.session.add(nuevo_rol)
            db.session.commit()
            flash('Rol creado correctamente')
            return redirect(url_for('admin.listrols'))
        else:
            flash('El nombre del rol ya existe, elija otro.')
            return redirect(url_for('admin.crearol'))

    return render_template('admin/crearol.html')

# Listar usuarios y roles
@bp.route('/listusers')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listusers():
    users = User.query.all()
    return render_template('admin/listusers.html', users=users)

@bp.route('/listrols')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listrols():
    rolls = Roll.query.all()
    return render_template('admin/listrols.html', rolls=rolls)

# Editar y eliminar usuarios y roles
@bp.route('/editrol/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editrol(id):
    rol = get_rol(id)

    if rol is None:
        flash('El rol no existe.')
        return redirect(url_for('admin.listrols'))

    if request.method == 'POST':
        roll_name = request.form.get('roll_name')
        roll_description = request.form.get('roll_description')

        if not roll_name or not roll_description:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('admin.editrol', id=id))

        rol.roll_name = roll_name
        rol.roll_description = roll_description
        db.session.commit()
        flash('Rol editado correctamente')
        return redirect(url_for('admin.listrols'))

    return render_template('admin/editrol.html', rol=rol)

@bp.route('/deleterol/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deleterol(id):
    rol = get_rol(id)
    
    if rol is None:
        flash('El rol no existe.')
        return redirect(url_for('admin.listrols'))

    db.session.delete(rol)
    db.session.commit()
    flash('Rol eliminado correctamente')
    return redirect(url_for('admin.listrols'))

@bp.route('/deleteuser/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deleteuser(id):
    user = get_user(id)

    if user is None:
        flash('El usuario no existe.')
        return redirect(url_for('admin.listusers'))

    db.session.delete(user)
    db.session.commit()
    flash('Usuario eliminado correctamente')
    return redirect(url_for('admin.listusers'))


