"""
CONFIGURACIÃ“N DEL SISTEMA SGA
Variables de configuraciÃ³n para Flask, Base de Datos y JWT
"""

import os
from datetime import timedelta

class Config:
    """ConfiguraciÃ³n principal del sistema"""
    
    # ==================== CONFIGURACIÃ“N BASE DE DATOS ====================
    # Usando MySQL (XAMPP)
    # Cambia la contraseÃ±a si la tienes diferente (por defecto XAMPP es vacÃ­o)
    DB_HOST = '127.0.0.1'
    DB_USER = 'root'
    DB_PASSWORD = 'FredySena2026*'  # Contraseña local de MariaDB/MySQL
    DB_NAME = 'sga_nuevo_amanecer'
    DB_PORT = 3307
    
    # URL de conexiÃ³n SQLAlchemy
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # ==================== CONFIGURACIÃ“N JWT ====================
    SECRET_KEY = 'sga-nuevo-amanecer-secret-key-2026-sena'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)  # Token vÃ¡lido por 8 horas
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)   # Refresh token por 7 dÃ­as
    
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
