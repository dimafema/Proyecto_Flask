from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from icaroapp import db


class Roll(db.Model):  # Roles de los usuarios (ej. Administrador, Registrado, Suscriptor, etc.)
    __tablename__ = 'rolls'
    id = db.Column(db.Integer, primary_key=True)
    roll_name = db.Column(db.String(20), unique=True, nullable=False)
    roll_description = db.Column(db.Text, nullable=False)

    users = db.relationship('User', backref='roll', lazy=True)

    def __init__(self, roll_name, roll_description):
        self.roll_name = roll_name
        self.roll_description = roll_description

    def __repr__(self):
        return f'<Roll: {self.roll_name}>'  

class User(db.Model, UserMixin):  # Usuarios del sistema
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    roll_id = db.Column(db.Integer, db.ForeignKey('rolls.id'), nullable=False) 

    def set_password(self, password):
        """Convierte una contraseña en un hash seguro"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica la contraseña con el hash almacenado"""
        return check_password_hash(self.password, password)

    def __repr__(self):
        return f'<User: {self.username}>'

class Group(db.Model):  # Grupo de colectivos de aprendizaje (ej. Bomberos, Policías, etc.)
    __tablename__ = 'groups'
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(20), unique=True, nullable=False)
    group_description = db.Column(db.Text, nullable=False)

    def __init__(self, group_name, group_description):
        self.group_name = group_name
        self.group_description = group_description

    def __repr__(self):
        return f'<Group: {self.group_name}>'

class Field(db.Model):  # Campo de conocimiento o disciplina (ej. Específico, General, Administración, etc.)
    __tablename__ = 'fields'
    id = db.Column(db.Integer, primary_key=True)
    field_name = db.Column(db.String(20), nullable=False)
    field_description = db.Column(db.Text, nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)

    def __init__(self, field_name, field_description, group_id):
        self.field_name = field_name
        self.field_description = field_description
        self.group_id = group_id

    def __repr__(self):
        return f'<Field: {self.field_name}>'

class Resource(db.Model):  # Recursos de aprendizaje (ej. Módulo, Tema, etc.)
    __tablename__ = 'resources'
    id = db.Column(db.Integer, primary_key=True)
    resource_name = db.Column(db.String(100), unique=True, nullable=False)
    resource_description = db.Column(db.Text, nullable=False)
    resource_url = db.Column(db.Text, nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)

    def __init__(self, resource_name, resource_description, resource_url, field_id):
        self.resource_name = resource_name
        self.resource_description = resource_description
        self.resource_url = resource_url
        self.field_id = field_id

    def __repr__(self):
        return f'<Resource: {self.resource_name}>'

class Nivel(db.Model):  # Niveles de aprendizaje (ej. Básico, Intermedio, Avanzado, etc.)
    __tablename__ = 'niveles'  # Corregido
    id = db.Column(db.Integer, primary_key=True)
    nivel_name = db.Column(db.String(20), unique=True, nullable=False)
    nivel_description = db.Column(db.Text, nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)

    def __init__(self, nivel_name, nivel_description, resource_id):
        self.nivel_name = nivel_name
        self.nivel_description = nivel_description
        self.resource_id = resource_id
    def __repr__(self):
        return f'<Nivel: {self.nivel_name}>'

class Quiz(db.Model):  # Preguntas de los cuestionarios de aprendizaje
    __tablename__ = 'quizzes'
    id = db.Column(db.Integer, primary_key=True)
    ask_title_group = db.Column(db.Text, nullable=True)  # Grupo de preguntas
    ask_name = db.Column(db.Text, nullable=False)  # Pregunta
    answer1 = db.Column(db.Text, nullable=False)  # Respuesta 1
    answer2 = db.Column(db.Text, nullable=False)  # Respuesta 2
    answer3 = db.Column(db.Text, nullable=True)  # Respuesta 3
    answer4 = db.Column(db.Text, nullable=True)  # Respuesta 4
    answer5 = db.Column(db.Text, nullable=True)  # Respuesta 5
    answer6 = db.Column(db.Text, nullable=True)  # Respuesta 6
    answer7 = db.Column(db.Text, nullable=True)  # Respuesta 7
    answer8 = db.Column(db.Text, nullable=True)  # Respuesta 8
    correct_answer = db.Column(db.Text, nullable=False)
    ask_description = db.Column(db.Text, unique=False)  # Explicación
    group_id = db.Column(db.Integer, db.ForeignKey('groups.id'), nullable=False)
    field_id = db.Column(db.Integer, db.ForeignKey('fields.id'), nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=False)
    nivel_id = db.Column(db.Integer, db.ForeignKey('niveles.id'), nullable=False)

    

    def get_valid_answers(self):
        """Retorna solo las respuestas que no son nulas"""
        return [answer for answer in [self.answer1, self.answer2, self.answer3, self.answer4] if answer and answer.strip()]

    def __repr__(self):
        return f'<Quiz: {self.ask_name}>'

class QuizAttempt(db.Model):
    __tablename__ = "quiz_attempts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    questions = db.relationship('QuizAttemptQuestion', backref='attempt', lazy=True)

class QuizAttemptQuestion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_answer = db.Column(db.String, nullable=True)  # Respuesta del usuario
    score = db.Column(db.Integer, default=0)
    quiz = db.relationship('Quiz', foreign_keys=[quiz_id])  # ✅ Relación corregida

class UserQuiz(db.Model):  # Cuestionarios de aprendizaje realizados por los usuarios
    __tablename__ = 'userquizzes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    user_answer = db.Column(db.Text, nullable=False)  # Corregido
    user_score = db.Column(db.Integer, nullable=False)  # Puntaje del usuario
    user_date = db.Column(db.DateTime, nullable=False)  # Fecha de realización del cuestionario
    attempt_id = db.Column(db.Integer, nullable=False)  # Identificador del intento
    
    def __init__(self, user_id, quiz_id, user_answer, user_score, user_date, attempt_id):
        self.user_id = user_id
        self.quiz_id = quiz_id
        self.user_answer = user_answer
        self.user_score = user_score
        self.user_date = user_date
        self.attempt_id = attempt_id  
    def __repr__(self):
        return f'<UserQuiz: {self.user_id} , Attempt {self.attempt_id}>'