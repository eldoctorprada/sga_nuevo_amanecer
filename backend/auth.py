"""
AUTENTICACIÓN Y AUTORIZACIÓN - SGA "NUEVO AMANECER"
Manejo de JWT (JSON Web Tokens) para login seguro y verificación de roles
"""

import jwt
import bcrypt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from models import db, Usuario, TipoUsuario

# ==================== FUNCIONES DE HASH DE CONTRASEÑAS ====================

def hash_password(password: str) -> str:
    """
    Genera un hash seguro de la contraseña usando bcrypt
    Ejemplo: "password123" -> "$2b$12$KxGk5xGk5xGk5xGk5xGk5u"
    """
    salt = bcrypt.gensalt(rounds=12)  # 12 rondas es seguro y rápido
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verifica si la contraseña ingresada coincide con el hash almacenado
    Retorna True si son iguales, False si no
    """
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


# ==================== FUNCIONES DE JWT ====================

def generate_token(usuario: Usuario) -> dict:
    """
    Genera un JWT (JSON Web Token) para el usuario autenticado
    El token contiene: id_usuario, email, tipo_usuario, y fecha de expiración
    
    Retorna:
    {
        'access_token': 'eyJhbGciOiJIUzI1NiIs...',
        'refresh_token': 'eyJhbGciOiJIUzI1NiIs...',
        'expires_in': 28800  # segundos (8 horas)
    }
    """
    # Configuración desde config.py
    secret_key = current_app.config['SECRET_KEY']
    access_expires = current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
    refresh_expires = current_app.config['JWT_REFRESH_TOKEN_EXPIRES']
    
    # Payload del token de acceso (datos que se guardan en el token)
    access_payload = {
        'id_usuario': usuario.id_usuario,
        'email': usuario.email,
        'tipo_usuario': usuario.tipo_usuario,
        'nombre_completo': f"{usuario.nombre} {usuario.apellido}",
        'exp': datetime.utcnow() + access_expires,  # Fecha de expiración
        'iat': datetime.utcnow(),  # Fecha de emisión
        'type': 'access'
    }
    
    # Payload del refresh token (para obtener nuevo access token sin re-login)
    refresh_payload = {
        'id_usuario': usuario.id_usuario,
        'exp': datetime.utcnow() + refresh_expires,
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    
    # Generar los tokens
    access_token = jwt.encode(access_payload, secret_key, algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, secret_key, algorithm='HS256')
    
    return {
        'access_token': access_token,
        'refresh_token': refresh_token,
        'expires_in': int(access_expires.total_seconds()),
        'token_type': 'Bearer'
    }


def verify_token(token: str) -> dict:
    """
    Verifica que un token sea válido y no haya expirado
    Retorna el payload si es válido, o None si es inválido
    """
    try:
        secret_key = current_app.config['SECRET_KEY']
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None  # Token expirado
    except jwt.InvalidTokenError:
        return None  # Token inválido


def refresh_access_token(refresh_token: str) -> dict:
    """
    Genera un nuevo access token usando un refresh token válido
    Útil para mantener la sesión activa sin pedir login otra vez
    """
    payload = verify_token(refresh_token)
    
    if not payload or payload.get('type') != 'refresh':
        return None
    
    # Buscar el usuario en la base de datos
    usuario = Usuario.query.get(payload['id_usuario'])
    if not usuario or not usuario.activo:
        return None
    
    # Generar nuevo access token
    return generate_token(usuario)


# ==================== DECORADORES PARA PROTEGER RUTAS ====================

def token_required(f):
    """
    DECORADOR: Protege una ruta requiriendo un token JWT válido
    Uso: @token_required
    El usuario autenticado se pasa como parámetro 'usuario_actual' a la función
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Obtener el token del header Authorization
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return jsonify({
                'success': False,
                'message': 'Token de autenticación requerido'
            }), 401
        
        # El header viene como "Bearer <token>"
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'success': False,
                'message': 'Formato de token inválido. Use: Bearer <token>'
            }), 401
        
        token = parts[1]
        
        # 2. Verificar el token
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                'success': False,
                'message': 'Token inválido o expirado'
            }), 401
        
        # 3. Buscar el usuario en la base de datos
        usuario = Usuario.query.get(payload.get('id_usuario'))
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 401
        
        if not usuario.activo:
            return jsonify({
                'success': False,
                'message': 'Usuario inactivo. Contacte al administrador'
            }), 401
        
        # 4. Pasar el usuario autenticado a la función
        return f(usuario_actual=usuario, *args, **kwargs)
    
    return decorated


def role_required(allowed_roles: list):
    """
    DECORADOR: Protege una ruta requiriendo un rol específico
    Debe usarse DESPUÉS de @token_required
    
    Uso: @role_required(['administrativo', 'docente'])
    
    allowed_roles puede ser:
    - ['administrativo']: solo admin
    - ['docente']: solo docentes
    - ['estudiante']: solo estudiantes
    - ['administrativo', 'docente']: admin o docente
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Obtener el usuario_actual que viene de @token_required
            usuario_actual = kwargs.get('usuario_actual')
            
            if not usuario_actual:
                return jsonify({
                    'success': False,
                    'message': 'Usuario no autenticado'
                }), 401
            
            # Verificar si el rol del usuario está permitido
            if usuario_actual.tipo_usuario not in allowed_roles:
                return jsonify({
                    'success': False,
                    'message': f'Acceso denegado. Rol requerido: {", ".join(allowed_roles)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated
    return decorator


def get_current_user():
    """
    Obtiene el usuario actual a partir del token en la request
    Útil para rutas donde no queremos un decorador pero necesitamos el usuario
    """
    auth_header = request.headers.get('Authorization')
    
    if not auth_header:
        return None
    
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None
    
    payload = verify_token(parts[1])
    
    if not payload:
        return None
    
    return Usuario.query.get(payload.get('id_usuario'))


# ==================== FUNCIÓN PARA ACTUALIZAR CONTRASEÑA ====================

def update_password(usuario: Usuario, new_password: str) -> bool:
    """
    Actualiza la contraseña de un usuario
    Retorna True si se actualizó correctamente
    """
    try:
        usuario.password_hash = hash_password(new_password)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error actualizando contraseña: {e}")
        return False