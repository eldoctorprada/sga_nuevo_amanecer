"""
RUTAS DE HORARIOS - SGA
CRUD Completo: Crear, Leer, Actualizar, Eliminar horarios
"""

from flask import Blueprint, request, jsonify
from datetime import datetime as dt
from models import db, Horario, Grado, Materia, Docente
from auth import token_required, role_required

horario_bp = Blueprint('horarios', __name__, url_prefix='/api/horarios')

DIAS_ORDEN = ['lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado']


# ==================== LISTAR TODOS LOS HORARIOS (READ) ====================

@horario_bp.route('/', methods=['GET'])
@token_required
@role_required(['administrativo', 'docente'])
def listar_horarios(usuario_actual):
    """
    GET /api/horarios/
    Lista todos los horarios con filtros opcionales
    """
    try:
        grado_id = request.args.get('grado', type=int)
        periodo = request.args.get('periodo')
        anio = request.args.get('anio', type=int)
        
        query = Horario.query
        
        if grado_id:
            query = query.filter_by(id_grado=grado_id)
        if periodo:
            query = query.filter_by(periodo=periodo)
        if anio:
            query = query.filter_by(anio_academico=anio)
        
        horarios = query.order_by(Horario.dia_semana, Horario.hora_inicio).all()
        
        return jsonify({
            'success': True,
            'total': len(horarios),
            'horarios': [h.to_dict() for h in horarios]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== OBTENER HORARIO POR ID (READ) ====================

@horario_bp.route('/<int:id_horario>', methods=['GET'])
@token_required
@role_required(['administrativo', 'docente'])
def obtener_horario(usuario_actual, id_horario):
    """GET /api/horarios/{id_horario}"""
    try:
        horario = Horario.query.get(id_horario)
        
        if not horario:
            return jsonify({'success': False, 'message': 'Horario no encontrado'}), 404
        
        return jsonify({'success': True, 'horario': horario.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR HORARIO POR GRADO (READ) ====================

@horario_bp.route('/grado/<int:id_grado>', methods=['GET'])
@token_required
def obtener_horario_grado(usuario_actual, id_grado):
    """GET /api/horarios/grado/{id_grado}"""
    try:
        periodo = request.args.get('periodo', '1')
        anio = request.args.get('anio', '2026')
        
        grado = Grado.query.get(id_grado)
        if not grado:
            return jsonify({'success': False, 'message': 'Grado no encontrado'}), 404
        
        horarios = Horario.query.filter_by(
            id_grado=id_grado,
            periodo=periodo,
            anio_academico=int(anio)
        ).all()
        
        horario_organizado = {dia: [] for dia in DIAS_ORDEN}
        for h in horarios:
            horario_organizado[h.dia_semana].append(h.to_dict())
        
        for dia in horario_organizado:
            horario_organizado[dia].sort(key=lambda x: x['hora_inicio'])
        
        return jsonify({
            'success': True,
            'grado': grado.to_dict(),
            'periodo': periodo,
            'anio': anio,
            'dias': DIAS_ORDEN,
            'horario': horario_organizado
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR HORARIO POR DOCENTE (READ) ====================

@horario_bp.route('/docente/<int:id_docente>', methods=['GET'])
@token_required
def obtener_horario_docente(usuario_actual, id_docente):
    """GET /api/horarios/docente/{id_docente}"""
    try:
        periodo = request.args.get('periodo', '1')
        anio = request.args.get('anio', '2026')
        
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        es_mismo_docente = usuario_actual.docente and usuario_actual.docente.id_docente == id_docente
        
        if not (es_admin or es_mismo_docente):
            return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
        
        docente = Docente.query.get(id_docente)
        if not docente:
            return jsonify({'success': False, 'message': 'Docente no encontrado'}), 404
        
        horarios = Horario.query.filter_by(
            id_docente=id_docente,
            periodo=periodo,
            anio_academico=int(anio)
        ).all()
        
        horario_organizado = {dia: [] for dia in DIAS_ORDEN}
        for h in horarios:
            horario_organizado[h.dia_semana].append(h.to_dict())
        
        for dia in horario_organizado:
            horario_organizado[dia].sort(key=lambda x: x['hora_inicio'])
        
        return jsonify({
            'success': True,
            'docente': docente.to_dict(),
            'periodo': periodo,
            'anio': anio,
            'dias': DIAS_ORDEN,
            'horario': horario_organizado
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CREAR HORARIO (CREATE) ====================

@horario_bp.route('/', methods=['POST'])
@token_required
@role_required(['administrativo'])
def crear_horario(usuario_actual):
    """POST /api/horarios/ - Crear nuevo horario"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        campos_requeridos = ['dia_semana', 'hora_inicio', 'hora_fin', 'id_grado', 'id_materia', 'id_docente', 'anio_academico', 'periodo']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'success': False, 'message': f'El campo {campo} es requerido'}), 400
        
        # Verificar que existan las relaciones
        grado = Grado.query.get(data['id_grado'])
        if not grado:
            return jsonify({'success': False, 'message': 'Grado no encontrado'}), 404
        
        materia = Materia.query.get(data['id_materia'])
        if not materia:
            return jsonify({'success': False, 'message': 'Materia no encontrada'}), 404
        
        docente = Docente.query.get(data['id_docente'])
        if not docente:
            return jsonify({'success': False, 'message': 'Docente no encontrado'}), 404
        
        hora_inicio = dt.strptime(data['hora_inicio'], '%H:%M').time()
        hora_fin = dt.strptime(data['hora_fin'], '%H:%M').time()
        
        # Verificar solapamiento de horarios
        horario_existente = Horario.query.filter_by(
            dia_semana=data['dia_semana'],
            id_grado=data['id_grado'],
            periodo=data['periodo'],
            anio_academico=data['anio_academico']
        ).filter(
            db.or_(
                db.and_(Horario.hora_inicio <= hora_inicio, Horario.hora_fin > hora_inicio),
                db.and_(Horario.hora_inicio < hora_fin, Horario.hora_fin >= hora_fin)
            )
        ).first()
        
        if horario_existente:
            return jsonify({'success': False, 'message': 'Ya existe un horario en ese día y hora'}), 400
        
        nuevo_horario = Horario(
            dia_semana=data['dia_semana'],
            hora_inicio=hora_inicio,
            hora_fin=hora_fin,
            id_grado=data['id_grado'],
            id_materia=data['id_materia'],
            id_docente=data['id_docente'],
            anio_academico=data['anio_academico'],
            periodo=data['periodo'],
            aula=data.get('aula')
        )
        
        db.session.add(nuevo_horario)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Horario creado exitosamente',
            'horario': nuevo_horario.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ACTUALIZAR HORARIO (UPDATE) ====================

@horario_bp.route('/<int:id_horario>', methods=['PUT'])
@token_required
@role_required(['administrativo'])
def actualizar_horario(usuario_actual, id_horario):
    """PUT /api/horarios/{id_horario} - Actualizar horario existente"""
    try:
        horario = Horario.query.get(id_horario)
        
        if not horario:
            return jsonify({'success': False, 'message': 'Horario no encontrado'}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        if 'dia_semana' in data:
            horario.dia_semana = data['dia_semana']
        if 'hora_inicio' in data:
            horario.hora_inicio = dt.strptime(data['hora_inicio'], '%H:%M').time()
        if 'hora_fin' in data:
            horario.hora_fin = dt.strptime(data['hora_fin'], '%H:%M').time()
        if 'id_materia' in data:
            materia = Materia.query.get(data['id_materia'])
            if materia:
                horario.id_materia = data['id_materia']
        if 'id_docente' in data:
            docente = Docente.query.get(data['id_docente'])
            if docente:
                horario.id_docente = data['id_docente']
        if 'aula' in data:
            horario.aula = data['aula']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Horario actualizado',
            'horario': horario.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ELIMINAR HORARIO (DELETE) ====================

@horario_bp.route('/<int:id_horario>', methods=['DELETE'])
@token_required
@role_required(['administrativo'])
def eliminar_horario(usuario_actual, id_horario):
    """DELETE /api/horarios/{id_horario}"""
    try:
        horario = Horario.query.get(id_horario)
        
        if not horario:
            return jsonify({'success': False, 'message': 'Horario no encontrado'}), 404
        
        db.session.delete(horario)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Horario eliminado'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500