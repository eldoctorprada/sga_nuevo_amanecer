"""
RUTAS DE CATÁLOGO - SGA
Endpoints de solo lectura para listas de referencia: grados y materias.
Se usan para poblar selects en el frontend (Calificaciones, Horarios, etc.)
"""

from flask import Blueprint, jsonify
from models import Grado, Materia, Usuario
from auth import token_required

catalogo_bp = Blueprint('catalogo', __name__, url_prefix='/api')


# ==================== LISTAR GRADOS ====================

@catalogo_bp.route('/grados', methods=['GET'])
@token_required
def listar_grados(usuario_actual):
    """
    GET /api/grados
    Lista todos los grados activos del sistema
    """
    try:
        grados = Grado.query.filter_by(activo=True).order_by(Grado.nivel).all()
        return jsonify({
            'success': True,
            'grados': [g.to_dict() for g in grados]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== LISTAR MATERIAS ====================

@catalogo_bp.route('/materias', methods=['GET'])
@token_required
def listar_materias(usuario_actual):
    """
    GET /api/materias
    Lista todas las materias activas del sistema
    """
    try:
        materias = Materia.query.filter_by(activo=True).order_by(Materia.nombre).all()
        return jsonify({
            'success': True,
            'materias': [m.to_dict() for m in materias]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ==================== DIRECTORIO DE CONTACTOS ====================

@catalogo_bp.route('/directorio', methods=['GET'])
@token_required
def listar_directorio(usuario_actual):
    """
    GET /api/directorio
    Lista un directorio básico (id, nombre, rol) de todos los usuarios activos,
    disponible para cualquier usuario autenticado. No expone datos sensibles
    (documento, teléfono, etc.) — se usa para elegir destinatarios de mensajes.
    """
    try:
        usuarios = Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all()
        return jsonify({
            'success': True,
            'contactos': [
                {
                    'id_usuario': u.id_usuario,
                    'nombre_completo': f'{u.nombre} {u.apellido}',
                    'tipo_usuario': u.tipo_usuario
                }
                for u in usuarios if u.id_usuario != usuario_actual.id_usuario
            ]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
