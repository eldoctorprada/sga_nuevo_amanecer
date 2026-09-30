"""
CONFIGURACIÓN DEL SISTEMA SGA
Variables de configuración para Flask, Base de Datos y JWT
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración principal del sistema"""
    
    # ==================== CONFIGURACIÓN BASE DE DATOS ====================
    # Si DATABASE_URL está disponible (Railway), usarlo directamente
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        # Fallback: construir desde variables individuales (desarrollo local)
        DB_HOST = os.environ.get('MYSQL_HOST', os.environ.get('DB_HOST', '127.0.0.1'))
        DB_USER = os.environ.get('MYSQL_USER', os.environ.get('DB_USER', 'root'))
        DB_PASSWORD = os.environ.get('MYSQL_PASSWORD', os.environ.get('DB_PASSWORD', ''))
        DB_NAME = os.environ.get('MYSQL_DATABASE', os.environ.get('DB_NAME', 'sga_nuevo_amanecer'))
        DB_PORT = os.environ.get('MYSQL_PORT', os.environ.get('DB_PORT', '3306'))
        SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # ==================== CONFIGURACIÓN JWT ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-solo-para-desarrollo-cambiala')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # ==================== CONFIGURACIÓN GENERAL ====================
    DEBUG = True
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    """Configuración para entorno de desarrollo"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Configuración para entorno de producción"""
    DEBUG = False
    TESTING = False
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=4)

class TestingConfig(Config):
    """Configuración para pruebas unitarias"""
    TESTING = True
    DEBUG = True
    DB_NAME = 'sga_test'
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:@127.0.0.1:3306/sga_test'

# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}