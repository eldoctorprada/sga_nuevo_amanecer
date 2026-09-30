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
        # Railway a veces entrega la URL como "mysql://" pero SQLAlchemy con
        # el driver PyMySQL necesita "mysql+pymysql://". Convertimos por si acaso.
        if database_url.startswith('mysql://'):
            database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
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

    # ==================== AUTO-SETUP DE BASE DE DATOS (RAILWAY) ====================
    # Crea las tablas y siembra los usuarios automáticamente al arrancar.
    # Envuelto en try/except para que el servidor no se caiga si la BD falla.
    try:
        setup_database(app)
    except Exception as e:
        print(f"⚠️  No se pudo inicializar la base de datos: {str(e)}")
        print("   El servidor seguirá ejecutándose (revisa la variable DATABASE_URL)")
    # ==============================================================================

    return app


def setup_database(app):
    """
    Crea las tablas y carga los datos iniciales SI la base de datos está vacía.
    Se ejecuta automáticamente al arrancar (pensado para Railway/producción).
    Es idempotente: si ya existen usuarios, no vuelve a sembrar.
    """
    from datetime import date, time
    from models import (
        Usuario, Grado, Materia, Estudiante, Docente, Administrativo,
        DocenteMateria, Horario, Calificacion, Asistencia,
        TipoUsuario, Jornada, DiaSemana, TipoEvaluacion, Periodo
    )

    with app.app_context():
        # 1) Crear todas las tablas si no existen
        db.create_all()
        print("📦 Tablas creadas/verificadas")

        # 2) Si ya hay datos, no volver a sembrar
        if Usuario.query.count() > 0:
            print("ℹ️  La base de datos ya tiene datos. No se siembra de nuevo.")
            return

        print("🌱 Sembrando datos iniciales...")

        # Contraseñas conocidas -> hash bcrypt (admin123 / docente123 / estudiante123)
        admin_hash = hash_password('admin123')
        docente_hash = hash_password('docente123')
        estudiante_hash = hash_password('estudiante123')

        # ---------------- GRADOS ----------------
        grados = [
            Grado(nombre='Primero A', nivel=1, jornada=Jornada.MANANA),
            Grado(nombre='Primero B', nivel=1, jornada=Jornada.TARDE),
            Grado(nombre='Segundo A', nivel=2, jornada=Jornada.MANANA),
            Grado(nombre='Segundo B', nivel=2, jornada=Jornada.TARDE),
            Grado(nombre='Tercero A', nivel=3, jornada=Jornada.MANANA),
            Grado(nombre='Tercero B', nivel=3, jornada=Jornada.TARDE),
            Grado(nombre='Cuarto A', nivel=4, jornada=Jornada.MANANA),
            Grado(nombre='Cuarto B', nivel=4, jornada=Jornada.TARDE),
            Grado(nombre='Quinto A', nivel=5, jornada=Jornada.MANANA),
            Grado(nombre='Quinto B', nivel=5, jornada=Jornada.TARDE),
        ]
        db.session.add_all(grados)

        # ---------------- MATERIAS ----------------
        materias = [
            Materia(nombre='Matemáticas', codigo='MAT101', horas_semana=5),
            Materia(nombre='Lengua Castellana', codigo='LEN101', horas_semana=5),
            Materia(nombre='Ciencias Naturales', codigo='CIE101', horas_semana=4),
            Materia(nombre='Ciencias Sociales', codigo='SOC101', horas_semana=4),
            Materia(nombre='Inglés', codigo='ING101', horas_semana=3),
            Materia(nombre='Educación Física', codigo='EDF101', horas_semana=2),
            Materia(nombre='Ética y Valores', codigo='ETI101', horas_semana=2),
            Materia(nombre='Tecnología e Informática', codigo='TEC101', horas_semana=2),
            Materia(nombre='Arte y Cultura', codigo='ART101', horas_semana=2),
        ]
        db.session.add_all(materias)

        # ---------------- USUARIOS ----------------
        admin = Usuario(tipo_usuario=TipoUsuario.ADMINISTRATIVO, nombre='Laura', apellido='Torres',
                        email='admin@nuevoamanecer.edu', password_hash=admin_hash, telefono='3001234567')
        doc1 = Usuario(tipo_usuario=TipoUsuario.DOCENTE, nombre='Carlos', apellido='Martínez',
                       email='docente@nuevoamanecer.edu', password_hash=docente_hash, telefono='3101234567')
        doc2 = Usuario(tipo_usuario=TipoUsuario.DOCENTE, nombre='Ana', apellido='García',
                       email='ana.garcia@nuevoamanecer.edu', password_hash=docente_hash, telefono='3111234567')
        doc3 = Usuario(tipo_usuario=TipoUsuario.DOCENTE, nombre='Juan', apellido='Pérez',
                       email='juan.perez@nuevoamanecer.edu', password_hash=docente_hash, telefono='3121234567')
        db.session.add_all([admin, doc1, doc2, doc3])

        estudiantes_data = [
            ('Ana', 'Torres', 'ana.torres@estudiante.edu', '3201234567', '1001234567', date(2015, 3, 15), 'María Torres', '3101234567'),
            ('Carlos', 'Gómez', 'carlos.gomez@estudiante.edu', '3201234568', '1001234568', date(2015, 7, 20), 'Andrés Gómez', '3101234568'),
            ('María', 'López', 'maria.lopez@estudiante.edu', '3201234569', '1001234569', date(2014, 11, 10), 'Fernando López', '3101234569'),
            ('Pedro', 'Sánchez', 'pedro.sanchez@estudiante.edu', '3201234570', '1001234570', date(2015, 1, 25), 'Carmen Sánchez', '3101234570'),
            ('Luisa', 'Castro', 'luisa.castro@estudiante.edu', '3201234571', '1001234571', date(2014, 9, 30), 'Patricia Castro', '3101234571'),
            ('Sofía', 'Ramírez', 'sofia.ramirez@estudiante.edu', '3201234572', '1001234572', date(2015, 5, 12), 'Roberto Ramírez', '3101234572'),
            ('Andrés', 'Díaz', 'andres.diaz@estudiante.edu', '3201234573', '1001234573', date(2014, 12, 3), 'Laura Díaz', '3101234573'),
            ('Valentina', 'Moreno', 'valentina.moreno@estudiante.edu', '3201234574', '1001234574', date(2015, 8, 18), 'Jorge Moreno', '3101234574'),
            ('Samuel', 'Rojas', 'samuel.rojas@estudiante.edu', '3201234575', '1001234575', date(2014, 10, 22), 'Claudia Rojas', '3101234575'),
            ('Isabella', 'Jiménez', 'isabella.jimenez@estudiante.edu', '3201234576', '1001234576', date(2015, 2, 14), 'Luis Jiménez', '3101234576'),
            ('Nicolás', 'Ortiz', 'nicolas.ortiz@estudiante.edu', '3201234577', '1001234577', date(2015, 6, 7), 'Daniela Ortiz', '3101234577'),
        ]
        usuarios_est = []
        for nom, ape, email, tel, doc, fnac, acu_nom, acu_tel in estudiantes_data:
            u = Usuario(tipo_usuario=TipoUsuario.ESTUDIANTE, nombre=nom, apellido=ape,
                        email=email, password_hash=estudiante_hash, telefono=tel)
            db.session.add(u)
            usuarios_est.append((u, doc, fnac, acu_nom, acu_tel))

        # Necesitamos los IDs autogenerados -> flush
        db.session.flush()

        # ---------------- ADMINISTRATIVO ----------------
        db.session.add(Administrativo(id_usuario=admin.id_usuario, cargo='Coordinador Administrativo',
                                      area='Administración', fecha_ingreso=date(2020, 1, 15)))

        # ---------------- DOCENTES ----------------
        d1 = Docente(id_usuario=doc1.id_usuario, especialidad='Matemáticas Puras',
                     codigo_empleado='DOC001', departamento='Ciencias Exactas')
        d2 = Docente(id_usuario=doc2.id_usuario, especialidad='Literatura',
                     codigo_empleado='DOC002', departamento='Humanidades')
        d3 = Docente(id_usuario=doc3.id_usuario, especialidad='Educación Física',
                     codigo_empleado='DOC003', departamento='Bienestar Estudiantil')
        db.session.add_all([d1, d2, d3])

        # ---------------- ESTUDIANTES (todos en Quinto A = grados[8]) ----------------
        quinto_a = grados[8]
        estudiantes = []
        for u, doc, fnac, acu_nom, acu_tel in usuarios_est:
            e = Estudiante(id_usuario=u.id_usuario, documento=doc, fecha_nacimiento=fnac,
                           id_grado=quinto_a.id_grado, acudiente_nombre=acu_nom, acudiente_telefono=acu_tel)
            db.session.add(e)
            estudiantes.append(e)

        # Commit CRÍTICO: esto es lo mínimo que el login necesita
        db.session.commit()
        print("✅ Usuarios y datos base cargados (login listo)")

        # ---------------- DATOS DE EJEMPLO (opcionales) ----------------
        # Si algo falla aquí, el login sigue funcionando porque ya hicimos commit arriba.
        try:
            db.session.flush()  # asegurar IDs de docentes/estudiantes

            # docente_materia
            db.session.add_all([
                DocenteMateria(id_docente=d1.id_docente, id_materia=materias[0].id_materia, anio_academico=2026),
                DocenteMateria(id_docente=d1.id_docente, id_materia=materias[2].id_materia, anio_academico=2026),
                DocenteMateria(id_docente=d2.id_docente, id_materia=materias[1].id_materia, anio_academico=2026),
                DocenteMateria(id_docente=d2.id_docente, id_materia=materias[3].id_materia, anio_academico=2026),
                DocenteMateria(id_docente=d3.id_docente, id_materia=materias[5].id_materia, anio_academico=2026),
            ])

            # horarios
            db.session.add_all([
                Horario(dia_semana=DiaSemana.LUNES, hora_inicio=time(8, 0), hora_fin=time(10, 0),
                        id_grado=quinto_a.id_grado, id_materia=materias[0].id_materia, id_docente=d1.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Aula 201'),
                Horario(dia_semana=DiaSemana.LUNES, hora_inicio=time(10, 30), hora_fin=time(12, 30),
                        id_grado=quinto_a.id_grado, id_materia=materias[2].id_materia, id_docente=d1.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Laboratorio'),
                Horario(dia_semana=DiaSemana.MARTES, hora_inicio=time(8, 0), hora_fin=time(10, 0),
                        id_grado=quinto_a.id_grado, id_materia=materias[1].id_materia, id_docente=d2.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Aula 201'),
                Horario(dia_semana=DiaSemana.MIERCOLES, hora_inicio=time(8, 0), hora_fin=time(10, 0),
                        id_grado=quinto_a.id_grado, id_materia=materias[0].id_materia, id_docente=d1.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Aula 201'),
                Horario(dia_semana=DiaSemana.JUEVES, hora_inicio=time(10, 30), hora_fin=time(12, 30),
                        id_grado=quinto_a.id_grado, id_materia=materias[3].id_materia, id_docente=d2.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Aula 201'),
                Horario(dia_semana=DiaSemana.VIERNES, hora_inicio=time(8, 0), hora_fin=time(10, 0),
                        id_grado=quinto_a.id_grado, id_materia=materias[5].id_materia, id_docente=d3.id_docente,
                        anio_academico=2026, periodo=Periodo.PRIMERO, aula='Cancha'),
            ])

            # calificaciones de ejemplo (Matemáticas, registradas por el docente Carlos)
            db.session.add_all([
                Calificacion(id_estudiante=estudiantes[0].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.PARCIAL1, nota=4.5, porcentaje=30, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion='Buen desempeño'),
                Calificacion(id_estudiante=estudiantes[0].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.PARCIAL2, nota=4.0, porcentaje=30, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion='Mejorar participación'),
                Calificacion(id_estudiante=estudiantes[0].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.FINAL, nota=5.0, porcentaje=40, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion='Excelente trabajo final'),
                Calificacion(id_estudiante=estudiantes[1].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.PARCIAL1, nota=3.0, porcentaje=30, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion='Puede mejorar'),
                Calificacion(id_estudiante=estudiantes[1].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.PARCIAL2, nota=3.5, porcentaje=30, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion=''),
                Calificacion(id_estudiante=estudiantes[1].id_estudiante, id_materia=materias[0].id_materia,
                             tipo_evaluacion=TipoEvaluacion.FINAL, nota=3.0, porcentaje=40, periodo=Periodo.PRIMERO,
                             anio_academico=2026, registrado_por=doc1.id_usuario, observacion=''),
            ])

            # asistencias de ejemplo
            db.session.add_all([
                Asistencia(id_estudiante=estudiantes[0].id_estudiante, id_materia=materias[0].id_materia,
                           fecha=date(2026, 3, 15), presente=True, registrado_por=doc1.id_usuario),
                Asistencia(id_estudiante=estudiantes[1].id_estudiante, id_materia=materias[0].id_materia,
                           fecha=date(2026, 3, 15), presente=False, registrado_por=doc1.id_usuario),
                Asistencia(id_estudiante=estudiantes[2].id_estudiante, id_materia=materias[0].id_materia,
                           fecha=date(2026, 3, 15), presente=True, registrado_por=doc1.id_usuario),
                Asistencia(id_estudiante=estudiantes[3].id_estudiante, id_materia=materias[0].id_materia,
                           fecha=date(2026, 3, 15), presente=True, registrado_por=doc1.id_usuario),
                Asistencia(id_estudiante=estudiantes[4].id_estudiante, id_materia=materias[0].id_materia,
                           fecha=date(2026, 3, 15), presente=False, registrado_por=doc1.id_usuario),
            ])

            db.session.commit()
            print("✅ Datos de ejemplo cargados")
        except Exception as e:
            db.session.rollback()
            print(f"⚠️  No se pudieron cargar los datos de ejemplo (opcional): {str(e)}")


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
        print("✅ Base de datos inicializada correctamente")


if __name__ == '__main__':
    # Crear aplicación (create_app ya intenta crear tablas y sembrar datos)
    app = create_app('development')

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
    print("=" * 60)

    # Ejecutar servidor
    app.run(host='0.0.0.0', port=port, debug=True)