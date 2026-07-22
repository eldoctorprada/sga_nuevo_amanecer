"""
RUTAS DE USUARIOS - SGA
Endpoints para: CRUD completo de usuarios (solo administradores)
"""

from flask import Blueprint, request, jsonify
from models import db, Usuario, Estudiante, Docente, Administrativo, Grado, TipoUsuario, EstadoEstudiante
from auth import token_required, role_required, hash_password

usuario_bp = Blueprint('usuarios', __name__, url_prefix='/api/usuarios')


# ==================== LISTAR USUARIOS ====================

@usuario_bp.route('/', methods=['GET'])
@token_required
@role_required(['administrativo'])
def listar_usuarios(usuario_actual):
    """
    GET /api/usuarios/
    Lista todos los usuarios del sistema con filtros opcionales
    
    Parámetros query:
    - rol: filtrar por tipo_usuario (estudiante, docente, administrativo)
    - activo: filtrar por estado (true/false)
    - buscar: buscar por nombre, email o documento
    """
    try:
        # Obtener parámetros de filtro
        rol = request.args.get('rol')
        activo = request.args.get('activo')
        buscar = request.args.get('buscar', '').lower()
        
        # Query base
        query = Usuario.query
        
        # Aplicar filtros
        if rol and rol in ['estudiante', 'docente', 'administrativo']:
            query = query.filter_by(tipo_usuario=rol)
        
        if activo is not None:
            activo_bool = activo.lower() == 'true'
            query = query.filter_by(activo=activo_bool)
        
        if buscar:
            query = query.filter(
                db.or_(
                    Usuario.nombre.like(f'%{buscar}%'),
                    Usuario.apellido.like(f'%{buscar}%'),
                    Usuario.email.like(f'%{buscar}%')
                )
            )
        
        # Ejecutar query
        usuarios = query.order_by(Usuario.fecha_registro.desc()).all()
        
        # Construir respuesta con datos adicionales según rol
        resultado = []
        for u in usuarios:
            usuario_data = u.to_dict()
            
            # Agregar información específica del rol
            if u.tipo_usuario == TipoUsuario.ESTUDIANTE and u.estudiante:
                usuario_data['documento'] = u.estudiante.documento
                usuario_data['grado'] = u.estudiante.grado.nombre if u.estudiante.grado else None
                usuario_data['estado_estudiante'] = u.estudiante.estado
            elif u.tipo_usuario == TipoUsuario.DOCENTE and u.docente:
                usuario_data['codigo_empleado'] = u.docente.codigo_empleado
                usuario_data['especialidad'] = u.docente.especialidad
            elif u.tipo_usuario == TipoUsuario.ADMINISTRATIVO and u.administrativo:
                usuario_data['cargo'] = u.administrativo.cargo
                usuario_data['area'] = u.administrativo.area
            
            resultado.append(usuario_data)
        
        return jsonify({
            'success': True,
            'total': len(resultado),
            'usuarios': resultado
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al listar usuarios: {str(e)}'
        }), 500


# ==================== OBTENER USUARIO POR ID ====================

@usuario_bp.route('/<int:id_usuario>', methods=['GET'])
@token_required
@role_required(['administrativo'])
def obtener_usuario(usuario_actual, id_usuario):
    """GET /api/usuarios/{id} - Obtiene un usuario específico"""
    try:
        usuario = Usuario.query.get(id_usuario)
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        resultado = usuario.to_dict()
        
        # Agregar información específica del rol
        if usuario.tipo_usuario == TipoUsuario.ESTUDIANTE and usuario.estudiante:
            resultado['estudiante'] = usuario.estudiante.to_dict()
        elif usuario.tipo_usuario == TipoUsuario.DOCENTE and usuario.docente:
            resultado['docente'] = usuario.docente.to_dict()
        elif usuario.tipo_usuario == TipoUsuario.ADMINISTRATIVO and usuario.administrativo:
            resultado['administrativo'] = usuario.administrativo.to_dict()
        
        return jsonify({
            'success': True,
            'usuario': resultado
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener usuario: {str(e)}'
        }), 500


# ==================== CREAR USUARIO ====================

@usuario_bp.route('/', methods=['POST'])
@token_required
@role_required(['administrativo'])
def crear_usuario(usuario_actual):
    """
    POST /api/usuarios/
    Crea un nuevo usuario (estudiante, docente o administrativo)
    
    Body:
    {
        "tipo_usuario": "estudiante|docente|administrativo",
        "nombre": "Ana",
        "apellido": "Torres",
        "email": "ana@email.com",
        "password": "123456",
        "telefono": "3001234567",
        // Datos específicos del rol
        "documento": "1234567890", (si es estudiante)
        "id_grado": 1, (si es estudiante)
        "codigo_empleado": "DOC001", (si es docente)
        "especialidad": "Matemáticas", (si es docente)
        "cargo": "Coordinador", (si es administrativo)
        "area": "Académica" (si es administrativo)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se enviaron datos'
            }), 400
        
        # Validar campos obligatorios
        campos_requeridos = ['tipo_usuario', 'nombre', 'apellido', 'email', 'password']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({
                    'success': False,
                    'message': f'El campo {campo} es requerido'
                }), 400
        
        # Verificar si el email ya existe
        if Usuario.query.filter_by(email=data['email'].lower()).first():
            return jsonify({
                'success': False,
                'message': 'El email ya está registrado'
            }), 400
        
        # Validar tipo_usuario
        tipo = data['tipo_usuario']
        if tipo not in ['estudiante', 'docente', 'administrativo']:
            return jsonify({
                'success': False,
                'message': 'Tipo de usuario inválido'
            }), 400
        
        # Crear usuario base
        nuevo_usuario = Usuario(
            tipo_usuario=tipo,
            nombre=data['nombre'].strip(),
            apellido=data['apellido'].strip(),
            email=data['email'].lower().strip(),
            password_hash=hash_password(data['password']),
            telefono=data.get('telefono', ''),
            activo=True
        )
        
        db.session.add(nuevo_usuario)
        db.session.flush()  # Para obtener el id_usuario sin commit
        
        # Crear registro específico según el tipo
        if tipo == 'estudiante':
            if not data.get('documento'):
                return jsonify({
                    'success': False,
                    'message': 'El documento es requerido para estudiantes'
                }), 400
            
            nuevo_estudiante = Estudiante(
                id_usuario=nuevo_usuario.id_usuario,
                documento=data['documento'],
                fecha_nacimiento=data.get('fecha_nacimiento'),
                id_grado=data.get('id_grado'),
                direccion=data.get('direccion'),
                acudiente_nombre=data.get('acudiente_nombre'),
                acudiente_telefono=data.get('acudiente_telefono'),
                estado=EstadoEstudiante.ACTIVO
            )
            db.session.add(nuevo_estudiante)
            
        elif tipo == 'docente':
            if not data.get('codigo_empleado'):
                return jsonify({
                    'success': False,
                    'message': 'El código de empleado es requerido para docentes'
                }), 400
            
            # Verificar código único
            if Docente.query.filter_by(codigo_empleado=data['codigo_empleado']).first():
                return jsonify({
                    'success': False,
                    'message': 'El código de empleado ya existe'
                }), 400
            
            nuevo_docente = Docente(
                id_usuario=nuevo_usuario.id_usuario,
                especialidad=data.get('especialidad'),
                codigo_empleado=data['codigo_empleado'],
                departamento=data.get('departamento'),
                titulo_profesional=data.get('titulo_profesional')
            )
            db.session.add(nuevo_docente)
            
        elif tipo == 'administrativo':
            if not data.get('cargo'):
                return jsonify({
                    'success': False,
                    'message': 'El cargo es requerido para administrativos'
                }), 400
            
            nuevo_administrativo = Administrativo(
                id_usuario=nuevo_usuario.id_usuario,
                cargo=data['cargo'],
                area=data.get('area'),
                fecha_ingreso=data.get('fecha_ingreso')
            )
            db.session.add(nuevo_administrativo)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{tipo.capitalize()} creado exitosamente',
            'id_usuario': nuevo_usuario.id_usuario
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al crear usuario: {str(e)}'
        }), 500


# ==================== ACTUALIZAR USUARIO ====================

@usuario_bp.route('/<int:id_usuario>', methods=['PUT'])
@token_required
@role_required(['administrativo'])
def actualizar_usuario(usuario_actual, id_usuario):
    """PUT /api/usuarios/{id} - Actualiza un usuario existente"""
    try:
        usuario = Usuario.query.get(id_usuario)
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No se enviaron datos'
            }), 400
        
        # Actualizar campos base
        if 'nombre' in data:
            usuario.nombre = data['nombre'].strip()
        if 'apellido' in data:
            usuario.apellido = data['apellido'].strip()
        if 'telefono' in data:
            usuario.telefono = data['telefono']
        if 'email' in data and data['email']:
            # Verifico que el nuevo correo no esté siendo usado por otro usuario
            email_nuevo = data['email'].lower().strip()
            if email_nuevo != usuario.email:
                existe = Usuario.query.filter(
                    Usuario.email == email_nuevo,
                    Usuario.id_usuario != usuario.id_usuario
                ).first()
                if existe:
                    return jsonify({
                        'success': False,
                        'message': 'Ese correo ya está en uso por otro usuario'
                    }), 400
                usuario.email = email_nuevo
        if 'activo' in data:
            usuario.activo = data['activo']
        
        # Actualizar datos específicos según el rol
        if usuario.tipo_usuario == TipoUsuario.ESTUDIANTE and usuario.estudiante:
            if 'documento' in data:
                usuario.estudiante.documento = data['documento']
            if 'id_grado' in data:
                usuario.estudiante.id_grado = data['id_grado']
            if 'direccion' in data:
                usuario.estudiante.direccion = data['direccion']
            if 'acudiente_nombre' in data:
                usuario.estudiante.acudiente_nombre = data['acudiente_nombre']
            if 'acudiente_telefono' in data:
                usuario.estudiante.acudiente_telefono = data['acudiente_telefono']
            if 'estado' in data:
                usuario.estudiante.estado = data['estado']
                
        elif usuario.tipo_usuario == TipoUsuario.DOCENTE and usuario.docente:
            if 'especialidad' in data:
                usuario.docente.especialidad = data['especialidad']
            if 'departamento' in data:
                usuario.docente.departamento = data['departamento']
            if 'titulo_profesional' in data:
                usuario.docente.titulo_profesional = data['titulo_profesional']
                
        elif usuario.tipo_usuario == TipoUsuario.ADMINISTRATIVO and usuario.administrativo:
            if 'cargo' in data:
                usuario.administrativo.cargo = data['cargo']
            if 'area' in data:
                usuario.administrativo.area = data['area']
        
        # Si se envía nueva contraseña, actualizarla
        if 'password' in data and data['password']:
            usuario.password_hash = hash_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Usuario actualizado exitosamente'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al actualizar usuario: {str(e)}'
        }), 500


# ==================== ELIMINAR USUARIO ====================

@usuario_bp.route('/<int:id_usuario>', methods=['DELETE'])
@token_required
@role_required(['administrativo'])
def eliminar_usuario(usuario_actual, id_usuario):
    """DELETE /api/usuarios/{id} - Elimina un usuario (soft delete o hard delete)"""
    try:
        usuario = Usuario.query.get(id_usuario)
        
        if not usuario:
            return jsonify({
                'success': False,
                'message': 'Usuario no encontrado'
            }), 404
        
        # No permitir eliminar el propio usuario
        if usuario.id_usuario == usuario_actual.id_usuario:
            return jsonify({
                'success': False,
                'message': 'No puedes eliminar tu propio usuario'
            }), 403
        
        # Soft delete: solo desactivar (recomendado)
        if request.args.get('hard', 'false').lower() == 'true':
            # Hard delete: eliminar físicamente (con CASCADE)
            db.session.delete(usuario)
            mensaje = 'Usuario eliminado permanentemente'
        else:
            # Soft delete: solo desactivar
            usuario.activo = False
            mensaje = 'Usuario desactivado exitosamente'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': mensaje
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error al eliminar usuario: {str(e)}'
        }), 500


# ==================== OBTENER ESTADÍSTICAS ====================

@usuario_bp.route('/estadisticas', methods=['GET'])
@token_required
@role_required(['administrativo'])
def obtener_estadisticas(usuario_actual):
    """GET /api/usuarios/estadisticas - Obtiene estadísticas de usuarios"""
    try:
        total_usuarios = Usuario.query.count()
        total_activos = Usuario.query.filter_by(activo=True).count()
        total_estudiantes = Usuario.query.filter_by(tipo_usuario='estudiante', activo=True).count()
        total_docentes = Usuario.query.filter_by(tipo_usuario='docente', activo=True).count()
        total_administrativos = Usuario.query.filter_by(tipo_usuario='administrativo', activo=True).count()
        
        return jsonify({
            'success': True,
            'estadisticas': {
                'total_usuarios': total_usuarios,
                'total_activos': total_activos,
                'total_inactivos': total_usuarios - total_activos,
                'estudiantes_activos': total_estudiantes,
                'docentes_activos': total_docentes,
                'administrativos_activos': total_administrativos
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al obtener estadísticas: {str(e)}'
        }), 500