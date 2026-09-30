"""
WSGI entry point para Railway/Gunicorn
Este archivo permite que Railway encuentre y ejecute la aplicación correctamente
"""

import os
from app import create_app, init_database

# Crear la aplicación
app = create_app('production')

# Inicializar base de datos en contexto de la app
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run()