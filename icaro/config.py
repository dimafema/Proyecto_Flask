
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
DATA_FOLDER = os.path.join(BASE_DIR, 'data')

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

POSTGRESQL = 'postgresql+psycopg2://postgres:7403@localhost:5432/icaro'  # aquí escapamos la @ con %40
# Clave API de OpenAI (Cargar desde variable de entorno)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class Config:
    DEBUG=True  #modo de depuración
    SECRET_KEY = os.environ.get('dev') or 'clave_secreta_super_segura'           
    SQLALCHEMY_DATABASE_URI = POSTGRESQL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = UPLOAD_FOLDER
    DATA_FOLDER = DATA_FOLDER
    
    #  # Configuración de sesiones
    # SESSION_PERMANENT = True
    # SESSION_TYPE = "filesystem"  # Usa almacenamiento en archivos
    # SESSION_PERMANENT = True
    # SESSION_USE_SIGNER = True
    # SESSION_FILE_DIR = "./flask_session"  # Carpeta donde se guardarán las sesiones