"""
INICIALIZACIÓN DE RUTAS
Este archivo hace que la carpeta 'routes' sea un paquete Python
"""

# Exportamos todas las rutas para facilitar la importación
from .auth_routes import auth_bp
from .usuario_routes import usuario_bp
from .asistencia_routes import asistencia_bp
from .calificacion_routes import calificacion_bp
from .horario_routes import horario_bp
from .comunicacion_routes import comunicacion_bp
from .reporte_routes import reporte_bp

# Lista de todos los blueprints para registrarlos fácilmente en app.py
blueprints = [
    auth_bp,
    usuario_bp,
    asistencia_bp,
    calificacion_bp,
    horario_bp,
    comunicacion_bp,
    reporte_bp
]