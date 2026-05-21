"""
RUTAS DE AUTENTICACIÓN - SGA
Endpoints para: Login, Logout, Refresh Token, Cambio de contraseña
"""

from flask import Blueprint, request, jsonify
from models import db, Usuario, TipoUsuario, Estudiante, Docente, Administrativo
from auth import verify_password, generate_token, refresh_access_token, hash_password

# Crear el Blueprint para rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Endpoint: POST /api/auth/login
    Body: { "email": "user@email.com", "password": "123456" }
    
    Retorna:
    {
        "success": true,
        "access_token": "eyJhbGci...",
        "refresh_token": "eyJhbGci...",
        "usuario": { ... }
    }
    """
    try:
        # Obtener datos del cuerpo de la petición
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se enviaron datos'
            }), 400
        
        email = data.get('email', '').lower().strip()
        password = data.get('password', '')
        
        # Validar campos obligatorios
        if not email or not password:
            return jsonify({
                'success': False,
                'message': 'Email y contraseña son requeridos'
            }), 400
        
        # Buscar usuario por email
        usuario = Usuario.query.filter_by(email=email, activo=True).first()
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
        
        # Verificar contraseña
        if not verify_password(password, usuario.password_hash):
            return jsonify({
                'success': False,
                'message': 'Credenciales inválidas'
            }), 401
        
        # Determinar a qué dashboard debe redirigir
        dashboard_url = 'dashboard.html'
        if usuario.tipo_usuario == TipoUsuario.ADMINISTRATIVO:
            dashboard_url = 'dashboard_admin.html'
        elif usuario.tipo_usuario == TipoUsuario.DOCENTE:
            dashboard_url = 'dashboard.html'
        elif usuario.tipo_usuario == TipoUsuario.ESTUDIANTE:
            dashboard_url = 'dashboard_estudiante.html'
        
        # Generar tokens JWT
        tokens = generate_token(usuario)
        
        # Obtener información adicional según el rol
        usuario_data = usuario.to_dict()
        
        if usuario.tipo_usuario == TipoUsuario.ESTUDIANTE and usuario.estudiante:
            usuario_data['estudiante'] = usuario.estudiante.to_dict()
            usuario_data['dashboard'] = 'estudiante'
        elif usuario.tipo_usuario == TipoUsuario.DOCENTE and usuario.docente:
            usuario_data['docente'] = usuario.docente.to_dict()
            usuario_data['dashboard'] = 'docente'
        elif usuario.tipo_usuario == TipoUsuario.ADMINISTRATIVO and usuario.administrativo:
            usuario_data['administrativo'] = usuario.administrativo.to_dict()
            usuario_data['dashboard'] = 'administrativo'
        
        return jsonify({
            'success': True,
            'message': 'Login exitoso',
            'access_token': tokens['access_token'],
            'refresh_token': tokens['refresh_token'],
            'expires_in': tokens['expires_in'],
            'token_type': tokens['token_type'],
            'usuario': usuario_data,
            'dashboard_url': dashboard_url
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en el servidor: {str(e)}'
        }), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """
    Endpoint: POST /api/auth/refresh
    Body: { "refresh_token": "eyJhbGci..." }
    
    Obtiene un nuevo access token usando el refresh token
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se enviaron datos'
            }), 400
        
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({
                'success': False,
                'message': 'Refresh token requerido'
            }), 400
        
        new_tokens = refresh_access_token(refresh_token)
        
        if not new_tokens:
            return jsonify({
                'success': False,
                'message': 'Refresh token inválido o expirado'
            }), 401
        
        return jsonify({
            'success': True,
            'access_token': new_tokens['access_token'],
            'refresh_token': new_tokens['refresh_token'],
            'expires_in': new_tokens['expires_in']
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error en el servidor: {str(e)}'
        }), 500


@auth_bp.route('/verify', methods=['GET'])
def verify_token_endpoint():
    """
    Endpoint: GET /api/auth/verify
    Header: Authorization: Bearer <token>
    
    Verifica si un token es válido y retorna información del usuario
    """
    from auth import get_current_user
    
    usuario_actual = get_current_user()
    
    if not usuario_actual:
        return jsonify({
            'success': False,
            'message': 'Token inválido o expirado'
        }), 401
    
    return jsonify({
        'success': True,
        'message': 'Token válido',
        'usuario': usuario_actual.to_dict()
    }), 200


@auth_bp.route('/cambiar-password', methods=['POST'])
def cambiar_password():
    """
    Endpoint: POST /api/auth/cambiar-password
    Header: Authorization: Bearer <token>
    Body: { "password_actual": "old123", "password_nueva": "new123" }
    """
    from auth import get_current_user, verify_password, update_password
    
    usuario_actual = get_current_user()
    
    if not usuario_actual:
        return jsonify({
            'success': False,
            'message': 'Token inválido o expirado'
        }), 401
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No se enviaron datos'
        }), 400
    
    password_actual = data.get('password_actual')
    password_nueva = data.get('password_nueva')
    
    if not password_actual or not password_nueva:
        return jsonify({
            'success': False,
            'message': 'Contraseña actual y nueva son requeridas'
        }), 400
    
    if len(password_nueva) < 6:
        return jsonify({
            'success': False,
            'message': 'La nueva contraseña debe tener al menos 6 caracteres'
        }), 400
    
    # Verificar contraseña actual
    if not verify_password(password_actual, usuario_actual.password_hash):
        return jsonify({
            'success': False,
            'message': 'Contraseña actual incorrecta'
        }), 401
    
    # Actualizar contraseña
    if update_password(usuario_actual, password_nueva):
        return jsonify({
            'success': True,
            'message': 'Contraseña actualizada exitosamente'
        }), 200
    else:
        return jsonify({
            'success': False,
            'message': 'Error al actualizar la contraseña'
        }), 500


# Datos de prueba para desarrollo rápido
@auth_bp.route('/test-login', methods=['GET'])
def test_login():
    """
    Endpoint de prueba: GET /api/auth/test-login
    Retorna credenciales de prueba para facilitar el desarrollo
    """
    credenciales = {
        'administrativo': {
            'email': 'admin@nuevoamanecer.edu',
            'password': 'admin123',
            'dashboard': 'dashboard_admin.html'
        },
        'docente': {
            'email': 'docente@nuevoamanecer.edu',
            'password': 'docente123',
            'dashboard': 'dashboard.html'
        },
        'estudiante': {
            'email': 'ana.torres@estudiante.edu',
            'password': 'estudiante123',
            'dashboard': 'dashboard_estudiante.html'
        }
    }
    
    return jsonify({
        'success': True,
        'message': 'Credenciales de prueba',
        'credenciales': credenciales
    }), 200