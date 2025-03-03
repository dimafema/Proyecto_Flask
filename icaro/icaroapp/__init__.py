from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
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
    login_manager.login_view = 'auth.login'
    
      # Definir el user_loader
    from .models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Registro de Blueprints con manejo de errores
    try:
        from . import icaro
        app.register_blueprint(icaro.bp)
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "icaro": {str(e)}')

    try:
        from . import auth
        app.register_blueprint(auth.bp)
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "auth": {str(e)}')
        
    try:
        from . import admin
        app.register_blueprint(admin.bp)
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "admin": {str(e)}')

    # Define la ruta raíz
    @app.route('/')
    def index():
        return render_template('index_public.html')

    return app