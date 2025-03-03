from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from config import Config

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    # 📌 Importar modelos correctamente
    from icaroapp import models  # ✅ Importa todos los modelos automáticamente

    # 📌 Registrar Blueprints después de la inicialización de db
    try:
        from .icaro import bp as icaro_bp
        app.register_blueprint(icaro_bp)
    except Exception as e:
        logging.error(f'Error al registrar Blueprint "icaro": {str(e)}')
        raise e  # Imprime el error real en la terminal para depuración

    return app