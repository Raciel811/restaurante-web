import os

class Config:
    # 1. CLAVE SECRETA
    # Busca una variable de entorno en la nube, si no existe, usa la de tu PC.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_123'

    # 2. BASE DE DATOS (Lógica Doble)
    # Intentamos obtener la URL de la base de datos del entorno (Render).
    db_url = os.environ.get('DATABASE_URL')

    if db_url:
        # --- SI ESTÁ EN LA NUBE (RENDER) ---
        # Render entrega URLs tipo "postgres://...", pero las versiones nuevas de 
        # SQLAlchemy prefieren "postgresql://...". Hacemos ese cambio automáticamente.
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
        
        # No es necesario especificar el driver aquí, Render usa postgresql nativo.
    else:
        # --- SI ESTÁ EN TU PC (LOCALHOST) ---
        # Usa tu configuración original de MySQL
        db_url = 'mysql+pymysql://root:123456@localhost:3306/restaurant_db'

    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False