from flask import Blueprint, render_template, g, redirect, url_for, request, flash, session, send_file, jsonify, current_app, flash, redirect, url_for, Response
from flask_login import current_user
from icaroapp.auth import login_required
from datetime import datetime
from icaroapp import db
from .models import Quiz, Group, Field, Resource, UserQuiz, Nivel, QuizAttempt, QuizAttemptQuestion
import functools
import logging
import os
import csv
from io import BytesIO
import random
import pandas as pd
from werkzeug.utils import secure_filename
from icaroapp.process_pdf import extract_text_from_pdf
from icaroapp.generate_questions import generate_complex_question, save_questions_to_csv
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User, Roll

from flask import Blueprint

bp = Blueprint('icaro', __name__, url_prefix='/icaro'  )  

# CREAR grupos, campos, recursos y niveles

@bp.route('/creategroup', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def creategroup():
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        group_description = request.form.get('group_description')

        creategroup = Group(group_name, group_description)

        group_name_check = Group.query.filter_by(group_name=group_name).first()

        if group_name_check is None:
            db.session.add(creategroup)
            db.session.commit()
            error = 'Grupo creado correctamente'
            flash(error)
            return redirect(url_for('icaro.listgroups'))
        else:
            error = f'El nombre del grupo ya existe, elija otro.'
            flash(error)
            return redirect(url_for('icaro.creategroup'))
    return render_template('icaro/creategroup.html')

@bp.route('/createfield', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def createfield():
    groups = Group.query.all()
    print(groups)
    if request.method == 'POST':
        field_name = request.form.get('field_name')
        field_description = request.form.get('field_description')
        group_id = request.form.get('group_id')

        createfield = Field(field_name, field_description, group_id)

        field_name_check = Field.query.filter_by(field_name=field_name).first()

        if field_name_check is None:
            db.session.add(createfield)
            db.session.commit()
            error = 'Campo creado correctamente'
            flash(error)
            return redirect(url_for('icaro.listfields'))
        else:
            error = f'El nombre del campo ya existe, elija otro.'
            flash(error)
            return redirect(url_for('icaro.createfield'))
    return render_template('icaro/createfield.html', grupo=groups)

@bp.route('/createresource', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def createresource():
        fields = Field.query.all()
        if request.method == 'POST':
            resource_name = request.form.get('resource_name')
            resource_description = request.form.get('resource_description')
            resource_url = request.form.get('resource_url')
            field_id = request.form.get('field_id')

            createresource = Resource(resource_name, resource_description, resource_url, field_id)
            createresource.field_id = field_id

            resource_name_check = Resource.query.filter_by(resource_name=resource_name).first()

            if resource_name_check is None:
                db.session.add(createresource)
                db.session.commit()
                flash('Recurso creado correctamente')
                return redirect(url_for('icaro.listresources'))
            else:
                flash('El nombre del recurso ya existe, elija otro.')
                return redirect(url_for('icaro.createresource'))
        return render_template('icaro/createresource.html', fields=fields) 

@bp.route('/createnivel', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def createnivel():
    resources = Resource.query.all()  # Obtener la lista de recursos

    if request.method == 'POST':
        nivel_name = request.form.get('nivel_name')
        nivel_description = request.form.get('nivel_description')
        resource_id = request.form.get('resource_id')

        # Verificar si se seleccionó un recurso válido
        if not resource_id or not Resource.query.get(resource_id):
            flash("Debe seleccionar un recurso válido.", "danger")
            return redirect(url_for('icaro.createnivel'))

        # Verificar si ya existe un nivel con el mismo nombre
        nivel_name_check = Nivel.query.filter_by(nivel_name=nivel_name).first()
        if nivel_name_check:
            flash("El nombre del nivel ya existe, elija otro.", "warning")
            return redirect(url_for('icaro.createnivel'))

        # Crear el nuevo nivel con el resource_id
        nuevo_nivel = Nivel(
            nivel_name=nivel_name,
            nivel_description=nivel_description,
            resource_id=int(resource_id)  # Convertir a entero
        )

        try:
            db.session.add(nuevo_nivel)
            db.session.commit()
            flash("Nivel creado correctamente", "success")
            return redirect(url_for('icaro.listniveles'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error al crear el nivel: {str(e)}", "danger")

    return render_template('icaro/createnivel.html', resources=resources)

# LISTAR grupos, campos, recursos y niveles

@bp.route('/listgroups')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listgroups():
    groups = Group.query.all()
    return render_template('icaro/listgroup.html', group=groups)

@bp.route('/listfields')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listfields():
    fields = Field.query.all()
    return render_template('icaro/listfields.html', field=fields)

@bp.route('/listresources')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listresources():
        resources = Resource.query.all()
        return render_template('icaro/listresources.html', resources=resources)    

@bp.route('/listniveles')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listniveles():
    niveles = Nivel.query.all()
    return render_template('icaro/listniveles.html', niveles=niveles) 

@bp.route('/listquizzes')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def listquizzes():
    # Obtener parámetros de la URL para la paginación
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 1, type=int)

    # Paginación de preguntas
    quizzes_pagination = Quiz.query.paginate(page=page, per_page=per_page, error_out=False)
    quizzes = quizzes_pagination.items

    return render_template(
        'quiz/listquizzes.html', 
        quizzes=quizzes, 
        quizzes_pagination=quizzes_pagination, 
        per_page=per_page
    )

# EDITAR grupos, campos, recursos y niveles

@bp.route('/editgroup/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editgroup(id):
    group = Group.query.get(id)
    if group is None:
        flash('El grupo no existe.')
        return redirect(url_for('icaro.listgroups'))

    if request.method == 'POST':
        group_name = request.form.get('group_name')
        group_description = request.form.get('group_description')

        if not group_name or not group_description:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('icaro.editgroup', id=id))

        group.group_name = group_name
        group.group_description = group_description
        db.session.commit()
        flash('Grupo editado correctamente')
        return redirect(url_for('icaro.listgroups'))

    return render_template('icaro/editgroup.html', group=group)

@bp.route('/editfield/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editfield(id):
    field = Field.query.get(id)
    groups = Group.query.all()
    
    if field is None:
        flash('El campo no existe.')
        return redirect(url_for('icaro.listfields'))

    if request.method == 'POST':
        field_name = request.form.get('field_name')
        field_description = request.form.get('field_description')
        group_id = request.form.get('group_id')

        if not field_name or not field_description or not group_id:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('icaro.editfield', id=id))

        field.field_name = field_name
        field.field_description = field_description
        field.group_id = group_id
        db.session.commit()
        flash('Campo editado correctamente')
        return redirect(url_for('icaro.listfields'))

    return render_template('icaro/editfield.html', field=field, groups=groups)

@bp.route('/editresource/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editresource(id):
    resource = Resource.query.get(id)
    fields = Field.query.all()
    if resource is None:
        flash('El recurso no existe.')
        return redirect(url_for('icaro.listresources'))
    if request.method == 'POST':
        resource_name = request.form.get('resource_name')
        resource_description = request.form.get('resource_description')
        resource_url = request.form.get('resource_url')
        field_id = request.form.get('field_id')
        if not resource_name or not resource_description or not resource_url or not field_id:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('icaro.editresource', id=id))
        resource.resource_name = resource_name
        resource.resource_description = resource_description
        resource.resource_url = resource_url
        resource.field_id = field_id
        db.session.commit()
        flash('Recurso editado correctamente')
        return redirect(url_for('icaro.listresources'))
    return render_template('icaro/editresource.html', resource=resource, fields=fields)

@bp.route('/editnivel/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editnivel(id):
    nivel = Nivel.query.get(id)

    if nivel is None:
        flash('El nivel no existe.')
        return redirect(url_for('icaro.listniveles'))

    if request.method == 'POST':
        nivel_name = request.form.get('nivel_name')
        nivel_description = request.form.get('nivel_description')

        if not nivel_name or not nivel_description:
            flash('Todos los campos son obligatorios.')
            return redirect(url_for('icaro.editnivel', id=id))

        nivel.nivel_name = nivel_name
        nivel.nivel_description = nivel_description
        db.session.commit()
        flash('Nivel editado correctamente')
        return redirect(url_for('icaro.listniveles'))

    return render_template('icaro/editnivel.html', nivel=nivel)

@bp.route('/editquiz/<int:id>', methods=('GET', 'POST'))
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def editquiz(id):
    quiz = Quiz.query.get(id)
    groups = Group.query.all()
    fields = Field.query.all()
    resources = Resource.query.all()
    niveles = Nivel.query.all()

    if quiz is None:
        flash('La pregunta no existe.')
        return redirect(url_for('icaro.listquizzes'))

    if request.method == 'POST':
        ask_title_group = request.form.get('ask_title_group')
        ask_name = request.form.get('ask_name')
        answer1 = request.form.get('answer1')
        answer2 = request.form.get('answer2')
        answer3 = request.form.get('answer3')
        answer4 = request.form.get('answer4')
        answer5 = request.form.get('answer5')
        answer6 = request.form.get('answer6')
        answer7 = request.form.get('answer7')
        answer8 = request.form.get('answer8')
        correct_answer = request.form.get('correct_answer')
        ask_description = request.form.get('ask_description')
        group_id = request.form.get('group_id')
        field_id = request.form.get('field_id')
        resource_id = request.form.get('resource_id')
        nivel_id = request.form.get('nivel_id')
        
        if not ask_name or not answer1 or not answer2 or not correct_answer:
            flash('Los campos principales son obligatorios.')
            return redirect(url_for('icaro.editquiz', id=id))

        quiz.ask_title_group = ask_title_group
        quiz.ask_name = ask_name
        quiz.answer1 = answer1
        quiz.answer2 = answer2
        quiz.answer3 = answer3
        quiz.answer4 = answer4
        quiz.answer5 = answer5
        quiz.answer6 = answer6
        quiz.answer7 = answer7
        quiz.answer8 = answer8
        quiz.correct_answer = correct_answer
        quiz.ask_description = ask_description
        quiz.group_id = group_id
        quiz.field_id = field_id
        quiz.resource_id = resource_id
        quiz.nivel_id = nivel_id

        db.session.commit()
        flash('Pregunta editada correctamente')
        return redirect(url_for('icaro.listquizzes'))

    return render_template('quiz/editquiz.html',groups=groups, fields=fields, resources=resources, niveles=niveles, quiz=quiz)

# ELIMINAR grupos, campos, recursos y niveles

@bp.route('/deletegroup/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deletegroup(id):
    group = Group.query.get(id)
    if group is None:
        flash('El grupo no existe.')
        return redirect(url_for('icaro.listgroups'))
    db.session.delete(group)
    db.session.commit()
    flash('Grupo eliminado correctamente')
    return redirect(url_for('icaro.listgroups'))

@bp.route('/deletefield/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deletefield(id):
    field = Field.query.get(id)
    if field is None:
        flash('El campo no existe.')
        return redirect(url_for('icaro.listfields'))
    db.session.delete(field)
    db.session.commit()
    flash('Campo eliminado correctamente')
    return redirect(url_for('icaro.listfields'))

@bp.route('/deleteresource/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deleteresource(id):
    resource = Resource.query.get(id)
    if resource is None:
        flash('El recurso no existe.')
        return redirect(url_for('icaro.listresources'))
    db.session.delete(resource)
    db.session.commit()
    flash('Recurso eliminado correctamente')
    return redirect(url_for('icaro.listresources'))

@bp.route('/deletenivel/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deletenivel(id):
    nivel = Nivel.query.get(id)
    if nivel is None:
        flash('El nivel no existe.')
        return redirect(url_for('icaro.listniveles'))
    db.session.delete(nivel)
    db.session.commit()
    flash('Nivel eliminado correctamente')
    return redirect(url_for('icaro.listniveles'))

@bp.route('/deletequiz/<int:id>')
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def deletequiz(id):
    quiz = Quiz.query.get(id)
    if quiz is None:
        flash('La pregunta no existe.')
        return redirect(url_for('icaro.listquizzes'))

    db.session.delete(quiz)
    db.session.commit()
    flash('Pregunta eliminada correctamente')
    return redirect(url_for('icaro.listquizzes'))

# SUBIR preguntas, responder preguntas y ver resultados

# Subir un archivo PDF y extraer preguntas
@bp.route('/upload', methods=['POST'])
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def upload_pdf():
    if "file" not in request.files:
        flash("No se ha subido ningún archivo.", "danger")
        return redirect(url_for('icaro.upload_quiz'))

    file = request.files["file"]
    if not file.filename.lower().endswith(".pdf"):
        flash("Solo se permiten archivos en formato PDF.", "warning")
        return redirect(url_for('icaro.upload_quiz'))

    filename = secure_filename(file.filename)
    file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    file.save(file_path)

    text = extract_text_from_pdf(file_path)
    if not text:
        flash("No se pudo extraer texto del PDF.", "danger")
        return redirect(url_for('icaro.upload_quiz'))

    ask_title_group = "Operaciones de Salvamento"  # Puedes ajustarlo dinámicamente
    questions = generate_complex_question(text, ask_title_group)

    if questions:
        csv_path = save_questions_to_csv(questions, filename)
        
        if csv_path and os.path.exists(csv_path):  # 📌 Verificar que el archivo existe antes de enviarlo
            flash("Preguntas generadas y guardadas correctamente.", "success")
            return send_file(csv_path, as_attachment=True)
        else:
            flash(f"❌ Error al generar el archivo CSV: {csv_path} no encontrado", "danger")
            return redirect(url_for('icaro.upload_quiz'))

    flash("No se generaron preguntas nuevas.", "warning")
    return redirect(url_for('icaro.upload_quiz'))

# Subir preguntas desde un archivo CSV
@bp.route('/upload_quiz', methods=['GET', 'POST'])
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def upload_quiz():
    # Número de preguntas por página (predeterminado en 10)
    per_page = request.args.get('per_page', 10, type=int)
    page = request.args.get('page', 1, type=int)

    # Obtener todas las preguntas con paginación
    quizzes_pagination = Quiz.query.paginate(page=page, per_page=per_page, error_out=False)
    quizzes = quizzes_pagination.items

    if request.method == 'POST':
        file = request.files['file']
        if file and file.filename.endswith('.csv'):
            filename = secure_filename(file.filename)
            upload_folder = 'uploads'
            if not os.path.exists(upload_folder):
                os.makedirs(upload_folder)  # Crear el directorio si no existe
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)

            with open(filepath, newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    try:
                        quiz = Quiz(
                            ask_title_group=row['ask_title_group'],
                            ask_name=row['ask_name'],
                            answer1=row['answer1'],
                            answer2=row['answer2'],
                            answer3=row.get('answer3'),
                            answer4=row.get('answer4'),
                            answer5=row.get('answer5'),
                            answer6=row.get('answer6'),
                            answer7=row.get('answer7'),
                            answer8=row.get('answer8'),
                            correct_answer=row['correct_answer'],
                            ask_description=row.get('ask_description'),
                            group_id=int(row['group_id']),
                            field_id=int(row['field_id']),
                            resource_id=int(row['resource_id']),
                            nivel_id=int(row['nivel_id'])
                        )
                        db.session.add(quiz)
                    except KeyError as e:
                        flash(f'Error en el archivo CSV: falta la columna {str(e)}')
                        return redirect(url_for('icaro.upload_quiz'))
                    except ValueError:
                        flash('Error en los valores del archivo CSV.')
                        return redirect(url_for('icaro.upload_quiz'))

                db.session.commit()
                flash('Preguntas cargadas correctamente.')
                return redirect(url_for('icaro.upload_quiz'))

    return render_template(
        'quiz/upload_quiz.html', 
        quizzes=quizzes, 
        quizzes_pagination=quizzes_pagination, 
        per_page=per_page
    )

# Exportar preguntas en formato Excel    
@bp.route('/quiz/exportquiz', methods=['GET'])
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def export_questions_excel():
    """Exporta todas las preguntas en formato Excel."""
    try:
        # Consultar todas las preguntas de la base de datos
        preguntas = Quiz.query.all()

        # Formatear los datos en un diccionario para DataFrame
        data = []
        for pregunta in preguntas:
            data.append({
                "ID": pregunta.id,
                "Título Grupo": pregunta.ask_title_group,
                "Pregunta": pregunta.ask_name,
                "Opción 1": pregunta.answer1,
                "Opción 2": pregunta.answer2,
                "Opción 3": pregunta.answer3,
                "Opción 4": pregunta.answer4,
                "Opción 5": pregunta.answer5,
                "Opción 6": pregunta.answer6,
                "Opción 7": pregunta.answer7,
                "Opción 8": pregunta.answer8,
                "Respuesta Correcta": pregunta.correct_answer,
                "Explicación": pregunta.ask_description,
                "Grupo ID": pregunta.group_id,
                "Field ID": pregunta.field_id,
                "Resource ID": pregunta.resource_id,
                "Nivel ID": pregunta.nivel_id
            })

        # Crear DataFrame con pandas
        df = pd.DataFrame(data)

        # Guardar en un archivo Excel en memoria
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name="Preguntas")

        # Preparar la respuesta para la descarga
        output.seek(0)
        response = Response(output.getvalue(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        response.headers["Content-Disposition"] = "attachment; filename=preguntas.xlsx"
        return response

    except Exception as e:
        return {"error": str(e)}, 500

# Importar preguntas desde un archivo Excel
@bp.route('/import/excel', methods=['GET', 'POST'])
@login_required(allowed_roles=[1])  # Solo Admins pueden acceder
def importquiz():
    """Importar preguntas desde un archivo Excel y guardarlas en PostgreSQL, asegurando conversión de tipos."""

    if request.method == 'POST':
        if 'file' not in request.files:
            flash("No se seleccionó ningún archivo", "error")
            return render_template('quiz/upload_quiz.html')

        file = request.files['file']
        if file.filename == '':
            flash("El archivo no tiene nombre", "error")
            return render_template('quiz/upload_quiz.html')

        try:
            df = pd.read_excel(file)

            required_columns = [
                "Pregunta", "Opción 1", "Opción 2", "Opción 3", "Opción 4",
                "Respuesta Correcta", "Explicación", "Grupo ID", "Field ID",
                "Resource ID", "Nivel ID"
            ]

            for col in required_columns:
                if col not in df.columns:
                    flash(f"Falta la columna requerida: {col}", "error")
                    return render_template('quiz/upload_quiz.html')

            # Limpiar valores incorrectos y convertir columnas numéricas
            numeric_columns = ["Grupo ID", "Field ID", "Resource ID", "Nivel ID"]
            
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')  # Convierte texto en NaN si hay errores
            
            # Reemplazar NaN por None para evitar errores en PostgreSQL
            df = df.where(pd.notna(df), None)

            for index, row in df.iterrows():
                try:
                    pregunta = Quiz(
                        ask_title_group=row.get("Título Grupo", None),
                        ask_name=str(row["Pregunta"]).strip(),
                        answer1=str(row["Opción 1"]).strip(),
                        answer2=str(row["Opción 2"]).strip(),
                        answer3=str(row.get("Opción 3", "")).strip() if row.get("Opción 3") else None,
                        answer4=str(row.get("Opción 4", "")).strip() if row.get("Opción 4") else None,
                        correct_answer=str(row["Respuesta Correcta"]).strip(),
                        ask_description=str(row.get("Explicación", "")).strip() if row.get("Explicación") else None,
                        group_id=int(row["Grupo ID"]) if row["Grupo ID"] is not None else None,
                        field_id=int(row["Field ID"]) if row["Field ID"] is not None else None,
                        resource_id=int(row["Resource ID"]) if row["Resource ID"] is not None else None,
                        nivel_id=int(row["Nivel ID"]) if row["Nivel ID"] is not None else None,
                    )
                    db.session.add(pregunta)

                except ValueError as ve:
                    flash(f"Error en conversión de datos en la fila {index + 1}: {ve}", "error")
                    db.session.rollback()
                    return render_template('quiz/upload_quiz.html')

                except Exception as e:
                    flash(f"Error inesperado en la fila {index + 1}: {str(e)}", "error")
                    db.session.rollback()
                    return render_template('quiz/upload_quiz.html')

            db.session.commit()
            flash("Preguntas importadas con éxito.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error al importar el archivo: {str(e)}", "error")

    return render_template('quiz/upload_quiz.html')

@bp.route('/quiz/<int:quiz_id>', methods=['GET', 'POST'])# Resolver preguntas
@login_required
def quiz(quiz_id):
    quiz = Quiz.query.get_or_404(quiz_id)
    attempt_id = session.get('attempt_id')
    attempt = QuizAttempt.query.get(attempt_id)

    # Obtener todas las preguntas del intento en orden de inserción (id autoincremental)
    questions = QuizAttemptQuestion.query.filter_by(attempt_id=attempt_id).order_by(QuizAttemptQuestion.id).all()

    # Obtener el índice de la pregunta actual en la lista ordenada
    question_index = next((index for (index, d) in enumerate(questions) if d.quiz_id == quiz_id), None)

    if question_index is not None:
        question = questions[question_index]  # Obtener la pregunta actual
    else:
        question = None

    total_questions = len(questions)
    
    # Habilitar botones de navegación
    prev_enabled = question_index > 0
    next_enabled = question_index < total_questions - 1

    # Asegurar que question_index no sea None
    if question_index is None:
        flash('No se pudo encontrar la pregunta actual.', 'danger')
        return redirect(url_for('icaro.quiz_setup'))

    # Obtener la respuesta anterior si existe
    previous_response = UserQuiz.query.filter_by(
        user_id=current_user.id,
        quiz_id=quiz.id,
        attempt_id=attempt_id
    ).first()

    if request.method == 'POST':
        user_answer = request.form.get('answer')

        if not user_answer:
            flash("Debes seleccionar una respuesta antes de continuar.", "warning")
            return redirect(url_for('icaro.quiz', quiz_id=quiz_id, attempt_id=attempt_id))

        user_score = 1 if user_answer == quiz.correct_answer else 0

        if previous_response:
            # Si ya hay una respuesta registrada, actualizarla
            previous_response.user_answer = user_answer
            previous_response.user_score = user_score
        else:
            # Si no existe, crear una nueva respuesta
            user_quiz = UserQuiz(
                user_id=current_user.id,
                quiz_id=quiz.id,
                user_answer=user_answer,
                user_score=user_score,
                user_date=datetime.utcnow(),
                attempt_id=attempt_id  # Asociar el intento actual
            )
            db.session.add(user_quiz)

        db.session.commit()
        flash('Respuesta registrada correctamente.')

        # Navegación entre preguntas
        if "next" in request.form and question_index + 1 < total_questions:
            next_quiz = questions[question_index + 1]
            return redirect(url_for('icaro.quiz', quiz_id=next_quiz.quiz_id, attempt_id=attempt_id))
        elif "prev" in request.form and question_index > 0:
            prev_quiz = questions[question_index - 1]
            return redirect(url_for('icaro.quiz', quiz_id=prev_quiz.quiz_id, attempt_id=attempt_id))
        elif "finish" in request.form:  # Si se pulsa "Terminar Evaluación"
            total_respuestas = UserQuiz.query.filter_by(attempt_id=attempt_id).count()
            return redirect(url_for('icaro.quiz_results', attempt_id=total_respuestas))

        # No salir hasta que el usuario pulse "Terminar Evaluación"
        return redirect(url_for('icaro.quiz', quiz_id=quiz_id, attempt_id=attempt_id))

    return render_template(
        'quiz/quiz.html',
        quiz=quiz,
        question_index=question_index,
        total_questions=total_questions,
        question=question,
        prev_enabled=prev_enabled,
        next_enabled=next_enabled,
        previous_answer=previous_response.user_answer if previous_response else None
    )

# Crear preguntas para resolver
@bp.route('/quiz/<int:resource_id>/<int:nivel_id>/<int:num_questions>', methods=['GET'])
@login_required
def start_quiz(resource_id, nivel_id, num_questions):
    """Inicia un intento de examen, seleccionando preguntas aleatorias y registrándolo en la base de datos."""

    # Obtener preguntas disponibles
    available_questions = Quiz.query.filter_by(resource_id=resource_id, nivel_id=nivel_id).all()

    if not available_questions:
        flash("No hay suficientes preguntas disponibles.", "danger")
        return redirect(url_for('icaro.quiz_setup'))

    # Seleccionar preguntas aleatorias según la cantidad ingresada
    selected_questions = random.sample(available_questions, min(num_questions, len(available_questions)))

    # Crear un nuevo intento de quiz
    new_attempt = QuizAttempt(user_id=current_user.id)
    db.session.add(new_attempt)
    db.session.commit()

    # Asociar preguntas al intento
    for question in selected_questions:
        attempt_question = QuizAttemptQuestion(
            attempt_id=new_attempt.id,
            quiz_id=question.id,
            user_answer=None,
            score=0
        )
        db.session.add(attempt_question)

    db.session.commit()

    # Guardar el ID del intento en la sesión
    session['attempt_id'] = new_attempt.id
    # Redirigir al primer quiz_id
    first_quiz_id = selected_questions[0].id
    return redirect(url_for('icaro.quiz', attempt_id=new_attempt.id, quiz_id=first_quiz_id))

# VER resultados de un intento de examen
@bp.route('/quiz_results/<int:attempt_id>')
@login_required
def quiz_results(attempt_id):
    """Muestra los resultados del intento del usuario."""
    
    attempts = QuizAttempt.query.filter_by(user_id=g.user.id).order_by(QuizAttempt.created_at.desc()).all()
   
    return render_template(
        'quiz/quiz_results.html', 
        attempts=attempts
    )

# VER detalles de las preguntas de un intento de examen
@bp.route('/quiz_attempt/<int:attempt_id>')
@login_required
def quiz_attempt(attempt_id):
    """Muestra los detalles de un intento específico, incluyendo preguntas y respuestas."""

    attempt = QuizAttempt.query.get(attempt_id)

    if not attempt:
        flash("No se encontró el intento.", "danger")
        return redirect(url_for('icaro.quiz_setup'))

    return render_template('quiz/quiz_results.html', attempt=attempt)

# SELECCIONAR grupo, campo, recurso y nivel
@bp.route('/quiz_setup', methods=['GET'])
@login_required
def quiz_setup():
    groups = Group.query.all()
    return render_template('quiz/quiz_setup.html', groups=groups)

@bp.route('/get_fields/<int:group_id>', methods=['GET'])
@login_required
def get_fields(group_id):
    fields = Field.query.filter_by(group_id=group_id).all()
    return {'fields': [{'id': f.id, 'name': f.field_name, 'description': f.field_description} for f in fields]}

@bp.route('/get_resources/<int:field_id>', methods=['GET'])
@login_required
def get_resources(field_id):
    resources = Resource.query.filter_by(field_id=field_id).all()
    return {'resources': [{'id': r.id, 'name': r.resource_name, 'description': r.resource_description,} for r in resources]}

@bp.route('/get_niveles/<int:resource_id>', methods=['GET'])
@login_required
def get_niveles(resource_id):
    niveles = Nivel.query.join(Quiz).filter(Quiz.resource_id == resource_id).distinct().all()
    return {'niveles': [{'id': n.id, 'name': n.nivel_name} for n in niveles]}


# Consultas SQL
def get_user(id):
    return User.query.get(id)  # Usa get() en lugar de filter_by().first()


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
            return redirect(url_for('icaro.index'))  
        else:
            flash('Usuario o contraseña incorrectos', 'danger') 
    return render_template('auth/login.html')

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))


def login_required(allowed_roles=None):
    if allowed_roles is None:
        allowed_roles = []

    def decorator(view):
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
    return decorator
