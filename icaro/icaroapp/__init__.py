from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
import logging
from flask import render_template


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Configuración del proyecto
    try:
        app.config.from_object('config.Config')
    except Exception as e:
        logging.error(f'Error al cargar la configuración: {str(e)}')
        raise

    db.init_app(app)
    migrate.init_app(app, db)  # Inicializar Flask-Migrate para migraciones
    login_manager.init_app(app)  # Inicializar Flask-Login

    # Configurar la vista de inicio de sesión
    login_manager.login_view = 'auth_bp.login'
    
    # Definir el user_loader
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registro de Blueprints con manejo de errores
    try:
        from . import icaro
        app.register_blueprint(icaro.bp, name='icaro')
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "icaro": {str(e)}')

    try:
        from . import auth
        app.register_blueprint(auth.bp, name='auth_bp')  # Evita conflicto de nombres
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "auth": {str(e)}')
        
    try:
        from . import admin
        app.register_blueprint(admin.bp, name='admin')
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "admin": {str(e)}')

    @app.route('/')
    def index():
        from .models import Quiz
        try:
            total_preguntas = Quiz.query.count()  # Obtener el total de preguntas
        except Exception as e:
            total_preguntas = 0  # Si hay un error (como que la tabla no exista aún)
            logging.error(f'Error al obtener el total de preguntas: {str(e)}')
        
        if current_user.is_authenticated:
            return render_template('icaro/index.html', total_preguntas=total_preguntas)
        else:
            return render_template('index_public.html', total_preguntas=total_preguntas)
    
    return app