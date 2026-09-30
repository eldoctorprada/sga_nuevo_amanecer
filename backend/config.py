"""
CONFIGURACIÓN DEL SISTEMA SGA
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuración principal del sistema"""
    
    # ==================== BASE DE DATOS ====================
    # En Railway: usar DATABASE_URL
    # En local: usar la conexión por defecto
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'mysql+pymysql://root:@127.0.0.1:3306/sga_nuevo_amanecer'
    )
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # ==================== JWT ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-solo-para-desarrollo')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # ==================== GENERAL ====================
    DEBUG = True
    JSON_AS_ASCII = False
    JSON_SORT_KEYS = False

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@127.0.0.1:3306/sga_test'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}