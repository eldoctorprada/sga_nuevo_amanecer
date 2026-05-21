"""
RUTAS DE COMUNICACIONES - SGA
CRUD Completo: Crear, Leer, Actualizar, Eliminar mensajes
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Comunicacion, Usuario
from auth import token_required, role_required

comunicacion_bp = Blueprint('comunicaciones', __name__, url_prefix='/api/comunicaciones')


# ==================== ENVIAR MENSAJE (CREATE) ====================

@comunicacion_bp.route('/', methods=['POST'])
@token_required
def enviar_mensaje(usuario_actual):
    """POST /api/comunicaciones/ - Enviar mensaje a otro usuario"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        if not data.get('destinatario_id') or not data.get('asunto') or not data.get('mensaje'):
            return jsonify({'success': False, 'message': 'destinatario_id, asunto y mensaje son requeridos'}), 400
        
        destinatario = Usuario.query.get(data['destinatario_id'])
        if not destinatario:
            return jsonify({'success': False, 'message': 'Destinatario no encontrado'}), 404
        
        if destinatario.id_usuario == usuario_actual.id_usuario:
            return jsonify({'success': False, 'message': 'No puedes enviarte un mensaje a ti mismo'}), 400
        
        nuevo_mensaje = Comunicacion(
            remitente_id=usuario_actual.id_usuario,
            destinatario_id=data['destinatario_id'],
            asunto=data['asunto'].strip(),
            mensaje=data['mensaje'].strip(),
            leido=False,
            fecha_envio=datetime.utcnow()
        )
        
        db.session.add(nuevo_mensaje)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Mensaje enviado',
            'id_comunicacion': nuevo_mensaje.id_comunicacion
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ENVIAR MENSAJE MASIVO (CREATE MULTIPLE) ====================

@comunicacion_bp.route('/masivo', methods=['POST'])
@token_required
@role_required(['docente', 'administrativo'])
def enviar_mensaje_masivo(usuario_actual):
    """POST /api/comunicaciones/masivo - Enviar a múltiples destinatarios"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        asunto = data.get('asunto')
        mensaje = data.get('mensaje')
        
        if not asunto or not mensaje:
            return jsonify({'success': False, 'message': 'asunto y mensaje son requeridos'}), 400
        
        destinatarios_ids = []
        
        if data.get('destinatarios_ids'):
            destinatarios_ids = data['destinatarios_ids']
        elif data.get('tipo_destinatario'):
            tipo = data['tipo_destinatario']
            usuarios = Usuario.query.filter_by(tipo_usuario=tipo, activo=True).all()
            destinatarios_ids = [u.id_usuario for u in usuarios]
        else:
            return jsonify({'success': False, 'message': 'Se requiere destinatarios_ids o tipo_destinatario'}), 400
        
        if usuario_actual.id_usuario in destinatarios_ids:
            destinatarios_ids.remove(usuario_actual.id_usuario)
        
        if not destinatarios_ids:
            return jsonify({'success': False, 'message': 'No hay destinatarios válidos'}), 400
        
        mensajes_creados = 0
        for dest_id in destinatarios_ids:
            nuevo_mensaje = Comunicacion(
                remitente_id=usuario_actual.id_usuario,
                destinatario_id=dest_id,
                asunto=asunto,
                mensaje=mensaje,
                leido=False,
                fecha_envio=datetime.utcnow()
            )
            db.session.add(nuevo_mensaje)
            mensajes_creados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Mensaje enviado a {mensajes_creados} destinatarios',
            'total_enviados': mensajes_creados
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== LISTAR MENSAJES RECIBIDOS (READ) ====================

@comunicacion_bp.route('/recibidos', methods=['GET'])
@token_required
def obtener_mensajes_recibidos(usuario_actual):
    """GET /api/comunicaciones/recibidos - Bandeja de entrada"""
    try:
        leido = request.args.get('leido')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Comunicacion.query.filter_by(destinatario_id=usuario_actual.id_usuario)
        
        if leido is not None:
            leido_bool = leido.lower() == 'true'
            query = query.filter_by(leido=leido_bool)
        
        total = query.count()
        mensajes = query.order_by(Comunicacion.fecha_envio.desc()).offset(offset).limit(limit).all()
        
        no_leidos = Comunicacion.query.filter_by(
            destinatario_id=usuario_actual.id_usuario,
            leido=False
        ).count()
        
        return jsonify({
            'success': True,
            'total': total,
            'no_leidos': no_leidos,
            'mensajes': [m.to_dict() for m in mensajes]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== LISTAR MENSAJES ENVIADOS (READ) ====================

@comunicacion_bp.route('/enviados', methods=['GET'])
@token_required
def obtener_mensajes_enviados(usuario_actual):
    """GET /api/comunicaciones/enviados - Mensajes enviados"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Comunicacion.query.filter_by(remitente_id=usuario_actual.id_usuario)
        total = query.count()
        mensajes = query.order_by(Comunicacion.fecha_envio.desc()).offset(offset).limit(limit).all()
        
        return jsonify({
            'success': True,
            'total': total,
            'mensajes': [m.to_dict() for m in mensajes]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== OBTENER DETALLE DE MENSAJE (READ) ====================

@comunicacion_bp.route('/<int:id_comunicacion>', methods=['GET'])
@token_required
def obtener_mensaje(usuario_actual, id_comunicacion):
    """GET /api/comunicaciones/{id_comunicacion}"""
    try:
        mensaje = Comunicacion.query.get(id_comunicacion)
        
        if not mensaje:
            return jsonify({'success': False, 'message': 'Mensaje no encontrado'}), 404
        
        if mensaje.remitente_id != usuario_actual.id_usuario and mensaje.destinatario_id != usuario_actual.id_usuario:
            return jsonify({'success': False, 'message': 'No tienes permiso'}), 403
        
        if mensaje.destinatario_id == usuario_actual.id_usuario and not mensaje.leido:
            mensaje.leido = True
            db.session.commit()
        
        return jsonify({'success': True, 'mensaje': mensaje.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== MARCAR COMO LEÍDO (UPDATE) ====================

@comunicacion_bp.route('/<int:id_comunicacion>/leer', methods=['PUT'])
@token_required
def marcar_como_leido(usuario_actual, id_comunicacion):
    """PUT /api/comunicaciones/{id_comunicacion}/leer"""
    try:
        mensaje = Comunicacion.query.get(id_comunicacion)
        
        if not mensaje:
            return jsonify({'success': False, 'message': 'Mensaje no encontrado'}), 404
        
        if mensaje.destinatario_id != usuario_actual.id_usuario:
            return jsonify({'success': False, 'message': 'No puedes marcar este mensaje'}), 403
        
        mensaje.leido = True
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Marcado como leído'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ACTUALIZAR MENSAJE (UPDATE) ====================

@comunicacion_bp.route('/<int:id_comunicacion>', methods=['PUT'])
@token_required
def actualizar_mensaje(usuario_actual, id_comunicacion):
    """PUT /api/comunicaciones/{id_comunicacion} - Editar mensaje (solo remitente)"""
    try:
        mensaje = Comunicacion.query.get(id_comunicacion)
        
        if not mensaje:
            return jsonify({'success': False, 'message': 'Mensaje no encontrado'}), 404
        
        if mensaje.remitente_id != usuario_actual.id_usuario:
            return jsonify({'success': False, 'message': 'No puedes editar este mensaje'}), 403
        
        data = request.get_json()
        
        if 'asunto' in data:
            mensaje.asunto = data['asunto']
        if 'mensaje' in data:
            mensaje.mensaje = data['mensaje']
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mensaje actualizado'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ELIMINAR MENSAJE (DELETE) ====================

@comunicacion_bp.route('/<int:id_comunicacion>', methods=['DELETE'])
@token_required
def eliminar_mensaje(usuario_actual, id_comunicacion):
    """DELETE /api/comunicaciones/{id_comunicacion}"""
    try:
        mensaje = Comunicacion.query.get(id_comunicacion)
        
        if not mensaje:
            return jsonify({'success': False, 'message': 'Mensaje no encontrado'}), 404
        
        if mensaje.remitente_id != usuario_actual.id_usuario and mensaje.destinatario_id != usuario_actual.id_usuario:
            return jsonify({'success': False, 'message': 'No tienes permiso'}), 403
        
        db.session.delete(mensaje)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Mensaje eliminado'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONTAR MENSAJES NO LEÍDOS ====================

@comunicacion_bp.route('/no-leidos/count', methods=['GET'])
@token_required
def contar_no_leidos(usuario_actual):
    """GET /api/comunicaciones/no-leidos/count"""
    try:
        no_leidos = Comunicacion.query.filter_by(
            destinatario_id=usuario_actual.id_usuario,
            leido=False
        ).count()
        
        return jsonify({'success': True, 'no_leidos': no_leidos}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500