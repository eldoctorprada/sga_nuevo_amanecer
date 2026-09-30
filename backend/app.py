"""
SISTEMA DE GESTIÓN ACADÉMICA (SGA) - "NUEVO AMANECER"
Servidor Principal Flask
Ejecutar: python app.py
"""

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
from datetime import datetime

# Importar configuración
from config import config

# Importar modelos (para que SQLAlchemy los reconozca)
from models import db

# Importar rutas (blueprints)
from routes import blueprints

# Importar autenticación
from auth import hash_password


def create_app(config_name='default'):
    """
    Fábrica de la aplicación Flask
    Crea y configura la instancia de la aplicación
    """
    app = Flask(__name__, static_folder='../frontend', static_url_path='')
    
    # Cargar configuración (config.py ya lee las credenciales desde .env)
    app.config.from_object(config[config_name])
    
    # ==================== DATABASE URL OVERRIDE (RAILWAY) ====================
    database_url = os.environ.get('DATABASE_URL')

    if database_url:
        # Si estamos en Railway, usar DATABASE_URL
        app.config['SQLALCHEMY_DATABASE_URI'] = database_url
        print(f"\n✅ DATABASE_URL encontrada - usando configuración de Railway")
    else:
        # Fallback para desarrollo local
        print(f"\n⚠️  DATABASE_URL no encontrada - usando configuración local (127.0.0.1)")

    # Log final de la URI configurada (sin contraseña)
    uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'NO CONFIGURADA')
    if uri and uri != 'NO CONFIGURADA':
        masked_uri = uri[:30] + '***' + uri[-30:] if len(uri) > 60 else uri
        print(f"📌 URI configurada: {masked_uri}")
    # ==================== FIN DATABASE URL ====================
    
    # Inicializar extensiones
    CORS(app)  # Permite peticiones desde el frontend
    db.init_app(app)
    
    # Registrar blueprints (rutas)
    for bp in blueprints:
        app.register_blueprint(bp)
    
    # ==================== RUTAS PARA EL FRONTEND ====================
    
    @app.route('/')
    def serve_index():
        """Sirve la página principal (login)"""
        return send_from_directory('../frontend', 'index.html')
    
    @app.route('/<path:filename>')
    def serve_frontend(filename):
        """Sirve cualquier archivo del frontend (HTML, CSS, JS)"""
        # Verificar si es un archivo HTML en la raíz
        if filename.endswith('.html'):
            filepath = os.path.join('../frontend', filename)
            if os.path.exists(filepath):
                return send_from_directory('../frontend', filename)
        
        # Verificar si es CSS
        if filename.startswith('css/'):
            return send_from_directory('../frontend', filename)
        
        # Verificar si es JS
        if filename.startswith('js/'):
            return send_from_directory('../frontend', filename)
        
        # Si no, intentar como archivo en la raíz
        return send_from_directory('../frontend', filename)
    
    # ==================== RUTAS DE UTILIDAD ====================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Endpoint para verificar que el servidor está activo"""
        return jsonify({
            'status': 'ok',
            'message': 'SGA Nuevo Amanecer - Servidor activo',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }), 200
    
    # ==================== MANEJADORES DE ERRORES ====================
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'message': 'Endpoint no encontrado'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            'success': False,
            'message': 'Error interno del servidor'
        }), 500
    
    return app


def init_database(app):
    """
    Inicializa la base de datos con datos de prueba
    Ejecutar solo la primera vez o cuando se necesita reiniciar
    """
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        
        # Verificar si ya hay datos
        from models import Usuario, Grado, Materia
        
        if Usuario.query.count() > 0:
            print("⚠️ La base de datos ya contiene datos. No se inicializará.")
            return
        
        print("📦 Inicializando base de datos con datos de prueba...")
        
        # Datos ya están en schema.sql
        # Este método es alternativo para crear datos desde Python
        
        print("✅ Base de datos inicializada correctamente")


if __name__ == '__main__':
    # Crear aplicación
    app = create_app('development')

    # Crear las tablas si no existen (alternativa al schema.sql)
    # Envuelto en try/except para no bloquear el servidor si falla
    try:
        with app.app_context():
            db.create_all()
            print("📦 Tablas creadas/verificadas")
    except Exception as e:
        print(f"⚠️  No se pudieron crear las tablas: {str(e)}")
        print("   El servidor seguirá ejecutándose")

    # Obtener el puerto desde variable de entorno o usar 5000
    port = int(os.environ.get('PORT', 5000))

    print("\n" + "=" * 60)
    print("🚀 SISTEMA DE GESTIÓN ACADÉMICA 'NUEVO AMANECER'")
    print("=" * 60)
    print(f"📍 Servidor corriendo en: http://localhost:{port}")
    print(f"🔐 Login: http://localhost:{port}/")
    print(f"💚 Health check: http://localhost:{port}/health")
    print("\n📋 CREDENCIALES DE PRUEBA:")
    print("   🧑‍💼 Admin:     admin@nuevoamanecer.edu / admin123")
    print("   👨‍🏫 Docente:   docente@nuevoamanecer.edu / docente123")
    print("   🎓 Estudiante: ana.torres@estudiante.edu / estudiante123")
    print("\n⚠️  NOTA: Ejecuta primero el script schema.sql en MySQL")
    print("   para crear la base de datos con datos iniciales")
    print("=" * 60)

    # Ejecutar servidor
    app.run(host='0.0.0.0', port=port, debug=True)
