"""
MODELOS DE DATOS - SGA "NUEVO AMANECER"
Define las clases que representan las tablas de la base de datos
Usa SQLAlchemy ORM para mapear objetos a tablas MySQL
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from enum import Enum

# Inicializar SQLAlchemy (se configurará en app.py)
db = SQLAlchemy()

def enum_values(enum_class):
    return [item.value for item in enum_class]


# ==================== ENUMS (para validaciÃ³n) ====================

class TipoUsuario(str, Enum):
    ESTUDIANTE = 'estudiante'
    DOCENTE = 'docente'
    ADMINISTRATIVO = 'administrativo'


class EstadoEstudiante(str, Enum):
    ACTIVO = 'activo'
    INACTIVO = 'inactivo'
    GRADUADO = 'graduado'
    RETIRADO = 'retirado'


class TipoEvaluacion(str, Enum):
    PARCIAL1 = 'parcial1'
    PARCIAL2 = 'parcial2'
    FINAL = 'final'
    TRABAJO = 'trabajo'
    QUIZZ = 'quizz'


class DiaSemana(str, Enum):
    LUNES = 'lunes'
    MARTES = 'martes'
    MIERCOLES = 'miercoles'
    JUEVES = 'jueves'
    VIERNES = 'viernes'
    SABADO = 'sabado'


class Jornada(str, Enum):
    MANANA = 'mañana'
    TARDE = 'tarde'
    NOCHE = 'noche'


class Periodo(str, Enum):
    PRIMERO = '1'
    SEGUNDO = '2'
    TERCERO = '3'
    CUARTO = '4'


# ==================== MODELOS ====================

class Usuario(db.Model):
    """
    Clase base abstracta para todos los usuarios del sistema
    Implementa herencia (Table per class en BD)
    """
    __tablename__ = 'usuario'
    
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tipo_usuario = db.Column(db.Enum(TipoUsuario, values_callable=enum_values), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellido = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    telefono = db.Column(db.String(20))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones (lazy='joined' para cargar datos relacionados automÃ¡ticamente)
    estudiante = db.relationship('Estudiante', backref='usuario', uselist=False, lazy='joined')
    docente = db.relationship('Docente', backref='usuario', uselist=False, lazy='joined')
    administrativo = db.relationship('Administrativo', backref='usuario', uselist=False, lazy='joined')
    
    def to_dict(self):
        """Convierte el objeto Usuario a diccionario para respuestas JSON"""
        data = {
            'id_usuario': self.id_usuario,
            'tipo_usuario': self.tipo_usuario,
            'nombre': self.nombre,
            'apellido': self.apellido,
            'nombre_completo': f"{self.nombre} {self.apellido}",
            'email': self.email,
            'telefono': self.telefono,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'activo': self.activo
        }
        return data
    
    def __repr__(self):
        return f'<Usuario {self.email}>'


class Grado(db.Model):
    """Niveles acadÃ©micos de la escuela"""
    __tablename__ = 'grado'
    
    id_grado = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(50), nullable=False)
    nivel = db.Column(db.Integer, nullable=False)
    jornada = db.Column(db.Enum(Jornada, values_callable=enum_values), default=Jornada.MANANA)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    estudiantes = db.relationship('Estudiante', backref='grado', lazy='dynamic')
    horarios = db.relationship('Horario', backref='grado', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id_grado': self.id_grado,
            'nombre': self.nombre,
            'nivel': self.nivel,
            'jornada': self.jornada,
            'activo': self.activo
        }
    
    def __repr__(self):
        return f'<Grado {self.nombre}>'


class Materia(db.Model):
    """Asignaturas del currÃ­culo acadÃ©mico"""
    __tablename__ = 'materia'
    
    id_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(10), unique=True, nullable=False)
    horas_semana = db.Column(db.Integer, nullable=False)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    calificaciones = db.relationship('Calificacion', backref='materia', lazy='dynamic')
    asistencias = db.relationship('Asistencia', backref='materia', lazy='dynamic')
    horarios = db.relationship('Horario', backref='materia', lazy='dynamic')
    docentes_asignados = db.relationship('DocenteMateria', backref='materia', lazy='dynamic')
    
    def to_dict(self):
        return {
            'id_materia': self.id_materia,
            'nombre': self.nombre,
            'codigo': self.codigo,
            'horas_semana': self.horas_semana,
            'activo': self.activo
        }
    
    def __repr__(self):
        return f'<Materia {self.nombre}>'


class Estudiante(db.Model):
    """InformaciÃ³n especÃ­fica de estudiantes (hereda de Usuario)"""
    __tablename__ = 'estudiante'
    
    id_estudiante = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    documento = db.Column(db.String(20), unique=True, nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    id_grado = db.Column(db.Integer, db.ForeignKey('grado.id_grado'))
    direccion = db.Column(db.String(200))
    acudiente_nombre = db.Column(db.String(150))
    acudiente_telefono = db.Column(db.String(20))
    estado = db.Column(db.Enum(EstadoEstudiante, values_callable=enum_values), default=EstadoEstudiante.ACTIVO)
    
    # Relaciones
    calificaciones = db.relationship('Calificacion', backref='estudiante', lazy='dynamic')
    asistencias = db.relationship('Asistencia', backref='estudiante', lazy='dynamic')
    
    def calcular_promedio_periodo(self, periodo, anio):
        """Calcula el promedio del estudiante en un perÃ­odo especÃ­fico"""
        calificaciones = self.calificaciones.filter_by(periodo=periodo, anio_academico=anio).all()
        
        if not calificaciones:
            return None
        
        # Agrupar por materia para calcular promedio por materia
        materias = {}
        for calif in calificaciones:
            if calif.id_materia not in materias:
                materias[calif.id_materia] = {'suma': 0, 'ponderacion_total': 0}
            
            valor_ponderado = calif.nota * (calif.porcentaje / 100)
            materias[calif.id_materia]['suma'] += valor_ponderado
            materias[calif.id_materia]['ponderacion_total'] += calif.porcentaje
        
        promedios = []
        for materia_id, datos in materias.items():
            if datos['ponderacion_total'] > 0:
                promedio = datos['suma'] * 100 / datos['ponderacion_total']
                promedios.append(promedio)
        
        if promedios:
            return round(sum(promedios) / len(promedios), 2)
        return 0
    
    def calcular_asistencia(self, periodo, anio):
        """Calcula el porcentaje de asistencia del estudiante en un perÃ­odo"""
        # Obtener horarios del grado para saber dÃ­as de clase
        asistencias = self.asistencias.join(Materia).filter(
            Asistencia.fecha.between(f'{anio}-01-01', f'{anio}-12-31')
        )
        
        total_clases = asistencias.count()
        presentes = asistencias.filter(Asistencia.presente == True).count()
        
        if total_clases > 0:
            return round((presentes / total_clases) * 100, 2)
        return 0
    
    def to_dict(self, include_calificaciones=False, include_asistencias=False):
        data = {
            'id_estudiante': self.id_estudiante,
            'usuario': self.usuario.to_dict() if self.usuario else None,
            'documento': self.documento,
            'fecha_nacimiento': self.fecha_nacimiento.isoformat() if self.fecha_nacimiento else None,
            'grado': self.grado.to_dict() if self.grado else None,
            'direccion': self.direccion,
            'acudiente_nombre': self.acudiente_nombre,
            'acudiente_telefono': self.acudiente_telefono,
            'estado': self.estado
        }
        
        if include_calificaciones:
            data['calificaciones'] = [c.to_dict() for c in self.calificaciones]
        
        if include_asistencias:
            data['asistencias'] = [a.to_dict() for a in self.asistencias]
        
        return data
    
    def __repr__(self):
        return f'<Estudiante {self.documento}>'


class Docente(db.Model):
    """InformaciÃ³n especÃ­fica de docentes (hereda de Usuario)"""
    __tablename__ = 'docente'
    
    id_docente = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    especialidad = db.Column(db.String(100))
    codigo_empleado = db.Column(db.String(20), unique=True, nullable=False)
    departamento = db.Column(db.String(50))
    titulo_profesional = db.Column(db.String(100))
    
    # Relaciones
    materias_asignadas = db.relationship('DocenteMateria', backref='docente', lazy='dynamic')
    horarios = db.relationship('Horario', backref='docente', lazy='dynamic')
    
    def to_dict(self, include_materias=False):
        data = {
            'id_docente': self.id_docente,
            'usuario': self.usuario.to_dict() if self.usuario else None,
            'especialidad': self.especialidad,
            'codigo_empleado': self.codigo_empleado,
            'departamento': self.departamento,
            'titulo_profesional': self.titulo_profesional
        }
        
        if include_materias:
            data['materias'] = [dm.materia.to_dict() for dm in self.materias_asignadas]
        
        return data
    
    def __repr__(self):
        return f'<Docente {self.codigo_empleado}>'


class Administrativo(db.Model):
    """Personal administrativo (hereda de Usuario)"""
    __tablename__ = 'administrativo'
    
    id_administrativo = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), unique=True, nullable=False)
    cargo = db.Column(db.String(50), nullable=False)
    area = db.Column(db.String(50))
    fecha_ingreso = db.Column(db.Date)
    
    def to_dict(self):
        return {
            'id_administrativo': self.id_administrativo,
            'usuario': self.usuario.to_dict() if self.usuario else None,
            'cargo': self.cargo,
            'area': self.area,
            'fecha_ingreso': self.fecha_ingreso.isoformat() if self.fecha_ingreso else None
        }
    
    def __repr__(self):
        return f'<Administrativo {self.cargo}>'


class DocenteMateria(db.Model):
    """RelaciÃ³n muchos a muchos entre Docente y Materia"""
    __tablename__ = 'docente_materia'
    
    id_docente_materia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_docente = db.Column(db.Integer, db.ForeignKey('docente.id_docente'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    anio_academico = db.Column(db.Integer, nullable=False)
    
    def to_dict(self):
        return {
            'id_docente_materia': self.id_docente_materia,
            'docente': self.docente.to_dict() if self.docente else None,
            'materia': self.materia.to_dict() if self.materia else None,
            'anio_academico': self.anio_academico
        }


class Horario(db.Model):
    """DistribuciÃ³n semanal de clases"""
    __tablename__ = 'horario'
    
    id_horario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    dia_semana = db.Column(db.Enum(DiaSemana, values_callable=enum_values), nullable=False)
    hora_inicio = db.Column(db.Time, nullable=False)
    hora_fin = db.Column(db.Time, nullable=False)
    id_grado = db.Column(db.Integer, db.ForeignKey('grado.id_grado'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    id_docente = db.Column(db.Integer, db.ForeignKey('docente.id_docente'), nullable=False)
    anio_academico = db.Column(db.Integer, nullable=False)
    periodo = db.Column(db.Enum(Periodo, values_callable=enum_values), nullable=False)
    aula = db.Column(db.String(20))
    
    def to_dict(self):
        return {
            'id_horario': self.id_horario,
            'dia_semana': self.dia_semana,
            'hora_inicio': self.hora_inicio.strftime('%H:%M') if self.hora_inicio else None,
            'hora_fin': self.hora_fin.strftime('%H:%M') if self.hora_fin else None,
            'grado': self.grado.to_dict() if self.grado else None,
            'materia': self.materia.to_dict() if self.materia else None,
            'docente': self.docente.to_dict() if self.docente else None,
            'anio_academico': self.anio_academico,
            'periodo': self.periodo,
            'aula': self.aula
        }


class Asistencia(db.Model):
    """Registro diario de asistencia de estudiantes"""
    __tablename__ = 'asistencia'
    
    id_asistencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id_estudiante'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    presente = db.Column(db.Boolean, nullable=False, default=False)
    justificacion = db.Column(db.Text)
    tipo_justificacion = db.Column(db.String(20), default='ninguna')
    registrado_por = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id_asistencia': self.id_asistencia,
            'estudiante': self.estudiante.to_dict() if self.estudiante else None,
            'materia': self.materia.to_dict() if self.materia else None,
            'fecha': self.fecha.isoformat() if self.fecha else None,
            'presente': self.presente,
            'justificacion': self.justificacion,
            'tipo_justificacion': self.tipo_justificacion,
            'estado': 'Presente' if self.presente else 'Ausente'
        }


class Calificacion(db.Model):
    """Registro de notas por materia, perÃ­odo y evaluaciÃ³n"""
    __tablename__ = 'calificacion'
    
    id_calificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_estudiante = db.Column(db.Integer, db.ForeignKey('estudiante.id_estudiante'), nullable=False)
    id_materia = db.Column(db.Integer, db.ForeignKey('materia.id_materia'), nullable=False)
    tipo_evaluacion = db.Column(db.Enum(TipoEvaluacion, values_callable=enum_values), nullable=False)
    nota = db.Column(db.Numeric(3, 1), nullable=False)
    porcentaje = db.Column(db.Numeric(4, 1), nullable=False)
    periodo = db.Column(db.Enum(Periodo, values_callable=enum_values), nullable=False)
    anio_academico = db.Column(db.Integer, nullable=False)
    observacion = db.Column(db.Text)
    registrado_por = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    def obtener_estado(self):
        """Determina el estado segÃºn la nota"""
        nota_float = float(self.nota)
        if nota_float >= 4.6:
            return 'Excelente'
        elif nota_float >= 4.0:
            return 'Muy Bien'
        elif nota_float >= 3.0:
            return 'Aprobado'
        elif nota_float >= 2.0:
            return 'En Riesgo'
        else:
            return 'Reprobado'
    
    def to_dict(self):
        return {
            'id_calificacion': self.id_calificacion,
            'estudiante': self.estudiante.to_dict() if self.estudiante else None,
            'materia': self.materia.to_dict() if self.materia else None,
            'tipo_evaluacion': self.tipo_evaluacion,
            'nota': float(self.nota),
            'porcentaje': float(self.porcentaje),
            'periodo': self.periodo,
            'anio_academico': self.anio_academico,
            'observacion': self.observacion,
            'estado': self.obtener_estado(),
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None
        }


class Comunicacion(db.Model):
    """MensajerÃ­a interna del sistema"""
    __tablename__ = 'comunicacion'
    
    id_comunicacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    remitente_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    destinatario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'), nullable=False)
    asunto = db.Column(db.String(200), nullable=False)
    mensaje = db.Column(db.Text, nullable=False)
    leido = db.Column(db.Boolean, default=False)
    fecha_envio = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    remitente = db.relationship('Usuario', foreign_keys=[remitente_id])
    destinatario = db.relationship('Usuario', foreign_keys=[destinatario_id])
    
    def to_dict(self):
        return {
            'id_comunicacion': self.id_comunicacion,
            'remitente': self.remitente.to_dict() if self.remitente else None,
            'destinatario': self.destinatario.to_dict() if self.destinatario else None,
            'asunto': self.asunto,
            'mensaje': self.mensaje,
            'leido': self.leido,
            'fecha_envio': self.fecha_envio.isoformat() if self.fecha_envio else None
        }


class Bitacora(db.Model):
    """AuditorÃ­a de eventos importantes"""
    __tablename__ = 'bitacora'
    
    id_bitacora = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    accion = db.Column(db.String(100), nullable=False)
    tabla_afectada = db.Column(db.String(50))
    registro_id = db.Column(db.Integer)
    detalles = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    fecha_evento = db.Column(db.DateTime, default=datetime.utcnow)
    
    # RelaciÃ³n
    usuario = db.relationship('Usuario', foreign_keys=[usuario_id])
    
    def to_dict(self):
        return {
            'id_bitacora': self.id_bitacora,
            'usuario': self.usuario.to_dict() if self.usuario else None,
            'accion': self.accion,
            'tabla_afectada': self.tabla_afectada,
            'registro_id': self.registro_id,
            'detalles': self.detalles,
            'ip_address': self.ip_address,
            'fecha_evento': self.fecha_evento.isoformat() if self.fecha_evento else None
        }
