"""
CONFIGURACIÃ“N DEL SISTEMA SGA
Variables de configuraciÃ³n para Flask, Base de Datos y JWT
"""

import os
from datetime import timedelta
from dotenv import load_dotenv
import os
from urllib.parse import urlparse
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

# ==================== PARSE RAILWAY DATABASE_URL ====================
database_url = os.environ.get('DATABASE_URL')
if database_url:
    # Railway provides DATABASE_URL in format: mysql+pymysql://user:pass@host:port/dbname
    parsed = urlparse(database_url)
    DB_HOST = parsed.hostname
    DB_USER = parsed.username
    DB_PASSWORD = parsed.password
    DB_NAME = parsed.path.lstrip('/')
    DB_PORT = parsed.port or 3306
else:
    # Fallback to individual env vars
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'sga_nuevo_amanecer')
    DB_PORT = os.environ.get('DB_PORT', '3307')
# Carga las variables definidas en el archivo .env (que NO se sube a Git)
load_dotenv()

class Config:
    """Configuración principal del sistema"""
    
    # ==================== CONFIGURACIÓN BASE DE DATOS ====================
    # Usando MySQL (XAMPP)
    # Todos estos valores se leen de variables de entorno (.env local).
    # Si alguna variable no está definida, se usa un valor por defecto
    # SOLO para que el proyecto no truene al importar; en desarrollo real
    # siempre debes tener tu propio archivo .env con tus credenciales.
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_USER = os.environ.get('DB_USER', 'root')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
    DB_NAME = os.environ.get('DB_NAME', 'sga_nuevo_amanecer')
    DB_PORT = os.environ.get('DB_PORT', '3307')
    
    # URL de conexión SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # ==================== CONFIGURACIÓN JWT ====================
    # También se lee de .env. Nunca dejes una clave real escrita aquí.
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-solo-para-desarrollo-cambiala')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)  # Token válido por 8 horas
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)   # Refresh token por 7 días
    
    # ==================== CONFIGURACIÃ“N GENERAL ====================
    DEBUG = True
    JSON_AS_ASCII = False  # Permitir caracteres especiales (tildes, Ã±)
    JSON_SORT_KEYS = False  # No ordenar las respuestas JSON automÃ¡ticamente


class DevelopmentConfig(Config):
    """ConfiguraciÃ³n para entorno de desarrollo"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """ConfiguraciÃ³n para entorno de producciÃ³n"""
    DEBUG = False
    TESTING = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=4)  # MÃ¡s restrictivo en producciÃ³n


class TestingConfig(Config):
    """ConfiguraciÃ³n para pruebas unitarias"""
    TESTING = True
    DEBUG = True
    # Base de datos de prueba
    DB_NAME = 'sga_test'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}'


# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
