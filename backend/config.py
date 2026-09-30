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
    
    # ==================== BASE DE DATOS ====================
    # Fallback para desarrollo local
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@127.0.0.1:3306/sga_nuevo_amanecer'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # ==================== JWT ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'clave-temporal-solo-para-desarrollo-cambiala')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # ==================== GENERAL ====================
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
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@127.0.0.1:3306/sga_test'

# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}