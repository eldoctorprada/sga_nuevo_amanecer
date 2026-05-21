"""
RUTAS DE ASISTENCIAS - SGA
Endpoints para: Registrar, consultar, modificar y eliminar asistencias
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, date
from models import db, Asistencia, Estudiante, Materia, Horario, Grado
from auth import token_required, role_required

asistencia_bp = Blueprint('asistencias', __name__, url_prefix='/api/asistencias')


# ==================== REGISTRAR ASISTENCIA ====================

@asistencia_bp.route('/', methods=['POST'])
@token_required
@role_required(['docente', 'administrativo'])
def registrar_asistencia(usuario_actual):
    """
    POST /api/asistencias/
    Registra la asistencia de un estudiante
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        campos_requeridos = ['id_estudiante', 'id_materia', 'fecha', 'presente']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'success': False, 'message': f'El campo {campo} es requerido'}), 400
        
        estudiante = Estudiante.query.get(data['id_estudiante'])
        if not estudiante:
            return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404
        
        materia = Materia.query.get(data['id_materia'])
        if not materia:
            return jsonify({'success': False, 'message': 'Materia no encontrada'}), 404
        
        fecha_asistencia = datetime.strptime(data['fecha'], '%Y-%m-%d').date()
        
        asistencia_existente = Asistencia.query.filter_by(
            id_estudiante=data['id_estudiante'],
            id_materia=data['id_materia'],
            fecha=fecha_asistencia
        ).first()
        
        if asistencia_existente:
            asistencia_existente.presente = data['presente']
            asistencia_existente.justificacion = data.get('justificacion')
            asistencia_existente.tipo_justificacion = data.get('tipo_justificacion', 'ninguna')
            asistencia_existente.registrado_por = usuario_actual.id_usuario
            asistencia_existente.fecha_registro = datetime.utcnow()
            mensaje = 'Asistencia actualizada'
        else:
            nueva_asistencia = Asistencia(
                id_estudiante=data['id_estudiante'],
                id_materia=data['id_materia'],
                fecha=fecha_asistencia,
                presente=data['presente'],
                justificacion=data.get('justificacion'),
                tipo_justificacion=data.get('tipo_justificacion', 'ninguna'),
                registrado_por=usuario_actual.id_usuario
            )
            db.session.add(nueva_asistencia)
            mensaje = 'Asistencia registrada'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': mensaje}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== REGISTRAR ASISTENCIA MASIVA ====================

@asistencia_bp.route('/masiva', methods=['POST'])
@token_required
@role_required(['docente', 'administrativo'])
def registrar_asistencia_masiva(usuario_actual):
    """
    POST /api/asistencias/masiva
    Registra asistencia para múltiples estudiantes
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        id_materia = data.get('id_materia')
        fecha_str = data.get('fecha')
        asistencias_data = data.get('asistencias', [])
        
        if not id_materia or not fecha_str or not asistencias_data:
            return jsonify({'success': False, 'message': 'id_materia, fecha y asistencias son requeridos'}), 400
        
        fecha_asistencia = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        materia = Materia.query.get(id_materia)
        if not materia:
            return jsonify({'success': False, 'message': 'Materia no encontrada'}), 404
        
        registros_actualizados = 0
        registros_creados = 0
        
        for item in asistencias_data:
            id_estudiante = item.get('id_estudiante')
            presente = item.get('presente', False)
            justificacion = item.get('justificacion')
            tipo_justificacion = item.get('tipo_justificacion', 'ninguna')
            
            asistencia_existente = Asistencia.query.filter_by(
                id_estudiante=id_estudiante,
                id_materia=id_materia,
                fecha=fecha_asistencia
            ).first()
            
            if asistencia_existente:
                asistencia_existente.presente = presente
                asistencia_existente.justificacion = justificacion
                asistencia_existente.tipo_justificacion = tipo_justificacion
                asistencia_existente.registrado_por = usuario_actual.id_usuario
                registros_actualizados += 1
            else:
                nueva_asistencia = Asistencia(
                    id_estudiante=id_estudiante,
                    id_materia=id_materia,
                    fecha=fecha_asistencia,
                    presente=presente,
                    justificacion=justificacion,
                    tipo_justificacion=tipo_justificacion,
                    registrado_por=usuario_actual.id_usuario
                )
                db.session.add(nueva_asistencia)
                registros_creados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Asistencia masiva: {registros_creados} creados, {registros_actualizados} actualizados',
            'creados': registros_creados,
            'actualizados': registros_actualizados
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR ASISTENCIAS POR ESTUDIANTE ====================

@asistencia_bp.route('/estudiante/<int:id_estudiante>', methods=['GET'])
@token_required
def obtener_asistencias_estudiante(usuario_actual, id_estudiante):
    """GET /api/asistencias/estudiante/{id_estudiante}"""
    try:
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        es_docente = usuario_actual.tipo_usuario == 'docente'
        es_mismo_estudiante = usuario_actual.estudiante and usuario_actual.estudiante.id_estudiante == id_estudiante
        
        if not (es_admin or es_docente or es_mismo_estudiante):
            return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
        
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404
        
        query = Asistencia.query.filter_by(id_estudiante=id_estudiante)
        
        periodo = request.args.get('periodo')
        anio = request.args.get('anio')
        id_materia = request.args.get('materia')
        
        if anio:
            query = query.filter(db.extract('year', Asistencia.fecha) == int(anio))
        if id_materia:
            query = query.filter_by(id_materia=int(id_materia))
        
        asistencias = query.order_by(Asistencia.fecha.desc()).all()
        
        total = len(asistencias)
        presentes = sum(1 for a in asistencias if a.presente)
        ausentes = total - presentes
        porcentaje = round((presentes / total * 100), 2) if total > 0 else 0
        
        return jsonify({
            'success': True,
            'estudiante': estudiante.to_dict(),
            'estadisticas': {'total': total, 'presentes': presentes, 'ausentes': ausentes, 'porcentaje_asistencia': porcentaje},
            'asistencias': [a.to_dict() for a in asistencias]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR ASISTENCIAS POR GRADO ====================

@asistencia_bp.route('/grado/<int:id_grado>', methods=['GET'])
@token_required
@role_required(['docente', 'administrativo'])
def obtener_asistencias_grado(usuario_actual, id_grado):
    """GET /api/asistencias/grado/{id_grado}"""
    try:
        fecha_str = request.args.get('fecha')
        id_materia = request.args.get('materia')
        
        if not fecha_str:
            return jsonify({'success': False, 'message': 'El parámetro fecha es requerido'}), 400
        
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        grado = Grado.query.get(id_grado)
        if not grado:
            return jsonify({'success': False, 'message': 'Grado no encontrado'}), 404
        
        estudiantes = Estudiante.query.filter_by(id_grado=id_grado, estado='activo').all()
        estudiantes_dict = {e.id_estudiante: e for e in estudiantes}
        
        query = Asistencia.query.filter_by(fecha=fecha)
        if id_materia:
            query = query.filter_by(id_materia=int(id_materia))
        
        asistencias = {a.id_estudiante: a for a in query.all()}
        
        resultado = []
        for id_est, estudiante in estudiantes_dict.items():
            asistencia = asistencias.get(id_est)
            resultado.append({
                'estudiante': estudiante.to_dict(),
                'asistencia': asistencia.to_dict() if asistencia else None,
                'registrado': asistencia is not None
            })
        
        return jsonify({
            'success': True,
            'grado': grado.to_dict(),
            'fecha': fecha_str,
            'total_estudiantes': len(resultado),
            'presentes': sum(1 for r in resultado if r['asistencia'] and r['asistencia']['presente']),
            'ausentes': sum(1 for r in resultado if r['asistencia'] and not r['asistencia']['presente']),
            'sin_registrar': sum(1 for r in resultado if not r['asistencia']),
            'asistencias': resultado
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ELIMINAR ASISTENCIA (DELETE) ====================

@asistencia_bp.route('/<int:id_asistencia>', methods=['DELETE'])
@token_required
@role_required(['docente', 'administrativo'])
def eliminar_asistencia(usuario_actual, id_asistencia):
    """
    DELETE /api/asistencias/{id_asistencia}
    Elimina un registro de asistencia específico
    """
    try:
        asistencia = Asistencia.query.get(id_asistencia)
        
        if not asistencia:
            return jsonify({'success': False, 'message': 'Registro de asistencia no encontrado'}), 404
        
        db.session.delete(asistencia)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Registro de asistencia eliminado'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error al eliminar: {str(e)}'}), 500


# ==================== JUSTIFICAR AUSENCIA ====================

@asistencia_bp.route('/justificar/<int:id_asistencia>', methods=['PUT'])
@token_required
def justificar_ausencia(usuario_actual, id_asistencia):
    """PUT /api/asistencias/justificar/{id_asistencia}"""
    try:
        asistencia = Asistencia.query.get(id_asistencia)
        
        if not asistencia:
            return jsonify({'success': False, 'message': 'Registro no encontrado'}), 404
        
        es_estudiante = usuario_actual.estudiante and usuario_actual.estudiante.id_estudiante == asistencia.id_estudiante
        es_docente = usuario_actual.tipo_usuario == 'docente'
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        
        if not (es_estudiante or es_docente or es_admin):
            return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        asistencia.justificacion = data.get('justificacion', asistencia.justificacion)
        asistencia.tipo_justificacion = data.get('tipo_justificacion', asistencia.tipo_justificacion)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Ausencia justificada'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500