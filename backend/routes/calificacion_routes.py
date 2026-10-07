"""
RUTAS DE CALIFICACIONES - SGA
Endpoints para: Registrar, consultar, modificar y eliminar calificaciones
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from models import db, Calificacion, Estudiante, Materia, Grado
from auth import token_required, role_required

calificacion_bp = Blueprint('calificaciones', __name__, url_prefix='/api/calificaciones')


# ==================== REGISTRAR CALIFICACIÓN ====================

@calificacion_bp.route('/', methods=['POST'])
@token_required
@role_required(['docente', 'administrativo'])
def registrar_calificacion(usuario_actual):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        campos_requeridos = ['id_estudiante', 'id_materia', 'tipo_evaluacion', 'nota', 'porcentaje', 'periodo', 'anio_academico']
        for campo in campos_requeridos:
            if campo not in data:
                return jsonify({'success': False, 'message': f'El campo {campo} es requerido'}), 400
        
        nota = float(data['nota'])
        if nota < 0 or nota > 5:
            return jsonify({'success': False, 'message': 'La nota debe estar entre 0 y 5'}), 400
        
        porcentaje = float(data['porcentaje'])
        if porcentaje <= 0 or porcentaje > 100:
            return jsonify({'success': False, 'message': 'El porcentaje debe estar entre 1 y 100'}), 400
        
        estudiante = Estudiante.query.get(data['id_estudiante'])
        if not estudiante:
            return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404
        
        materia = Materia.query.get(data['id_materia'])
        if not materia:
            return jsonify({'success': False, 'message': 'Materia no encontrada'}), 404
        
        calificacion_existente = Calificacion.query.filter_by(
            id_estudiante=data['id_estudiante'],
            id_materia=data['id_materia'],
            tipo_evaluacion=data['tipo_evaluacion'],
            periodo=data['periodo'],
            anio_academico=data['anio_academico']
        ).first()

        # Validar que la suma acumulada de porcentajes no supere el 100%
        # (por estudiante, materia, periodo y anio academico). Corrige BUG-001.
        suma_otros_query = db.session.query(
            db.func.coalesce(db.func.sum(Calificacion.porcentaje), 0)
        ).filter(
            Calificacion.id_estudiante == data['id_estudiante'],
            Calificacion.id_materia == data['id_materia'],
            Calificacion.periodo == data['periodo'],
            Calificacion.anio_academico == data['anio_academico']
        )
        if calificacion_existente:
            # se va a reemplazar: excluir su porcentaje actual de la suma
            suma_otros_query = suma_otros_query.filter(
                Calificacion.id_calificacion != calificacion_existente.id_calificacion
            )
        suma_otros = float(suma_otros_query.scalar() or 0)

        if suma_otros + porcentaje > 100:
            disponible = round(100 - suma_otros, 1)
            return jsonify({
                'success': False,
                'message': f'La suma de porcentajes de la materia superaria el 100%. '
                           f'Ya hay {suma_otros}% asignado en este periodo; '
                           f'porcentaje disponible: {disponible}%.'
            }), 400

        if calificacion_existente:
            calificacion_existente.nota = nota
            calificacion_existente.porcentaje = porcentaje
            calificacion_existente.observacion = data.get('observacion')
            calificacion_existente.registrado_por = usuario_actual.id_usuario
            calificacion_existente.fecha_registro = datetime.utcnow()
            mensaje = 'Calificación actualizada'
        else:
            nueva_calificacion = Calificacion(
                id_estudiante=data['id_estudiante'],
                id_materia=data['id_materia'],
                tipo_evaluacion=data['tipo_evaluacion'],
                nota=nota,
                porcentaje=porcentaje,
                periodo=data['periodo'],
                anio_academico=data['anio_academico'],
                observacion=data.get('observacion'),
                registrado_por=usuario_actual.id_usuario
            )
            db.session.add(nueva_calificacion)
            mensaje = 'Calificación registrada'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': mensaje}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ACTUALIZAR CALIFICACIÓN (UPDATE) ====================

@calificacion_bp.route('/<int:id_calificacion>', methods=['PUT'])
@token_required
@role_required(['docente', 'administrativo'])
def actualizar_calificacion(usuario_actual, id_calificacion):
    """PUT /api/calificaciones/{id_calificacion}"""
    try:
        calificacion = Calificacion.query.get(id_calificacion)
        
        if not calificacion:
            return jsonify({'success': False, 'message': 'Calificación no encontrada'}), 404
        
        data = request.get_json()
        
        if 'nota' in data:
            nota = float(data['nota'])
            if nota < 0 or nota > 5:
                return jsonify({'success': False, 'message': 'La nota debe estar entre 0 y 5'}), 400
            calificacion.nota = nota
        
        if 'observacion' in data:
            calificacion.observacion = data['observacion']
        
        calificacion.registrado_por = usuario_actual.id_usuario
        calificacion.fecha_registro = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Calificación actualizada'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== ELIMINAR CALIFICACIÓN (DELETE) ====================

@calificacion_bp.route('/<int:id_calificacion>', methods=['DELETE'])
@token_required
@role_required(['docente', 'administrativo'])
def eliminar_calificacion(usuario_actual, id_calificacion):
    """DELETE /api/calificaciones/{id_calificacion}"""
    try:
        calificacion = Calificacion.query.get(id_calificacion)
        
        if not calificacion:
            return jsonify({'success': False, 'message': 'Calificación no encontrada'}), 404
        
        db.session.delete(calificacion)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Calificación eliminada'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== REGISTRAR CALIFICACIONES MASIVAS ====================

@calificacion_bp.route('/masiva', methods=['POST'])
@token_required
@role_required(['docente', 'administrativo'])
def registrar_calificaciones_masivas(usuario_actual):
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No se enviaron datos'}), 400
        
        id_materia = data.get('id_materia')
        tipo_evaluacion = data.get('tipo_evaluacion')
        periodo = data.get('periodo')
        anio_academico = data.get('anio_academico')
        calificaciones_data = data.get('calificaciones', [])
        
        if not all([id_materia, tipo_evaluacion, periodo, anio_academico, calificaciones_data]):
            return jsonify({'success': False, 'message': 'Faltan campos requeridos'}), 400
        
        materia = Materia.query.get(id_materia)
        if not materia:
            return jsonify({'success': False, 'message': 'Materia no encontrada'}), 404
        
        registros_actualizados = 0
        registros_creados = 0
        
        for item in calificaciones_data:
            id_estudiante = item.get('id_estudiante')
            nota = float(item.get('nota', 0))
            observacion = item.get('observacion')
            porcentaje = float(item.get('porcentaje', 100 / len(calificaciones_data)))

            # Validar rango de nota (0-5) y porcentaje (1-100) tambien en carga masiva
            if nota < 0 or nota > 5:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'La nota del estudiante {id_estudiante} debe estar entre 0 y 5'}), 400
            if porcentaje <= 0 or porcentaje > 100:
                db.session.rollback()
                return jsonify({'success': False, 'message': 'El porcentaje debe estar entre 1 y 100'}), 400
            
            calificacion_existente = Calificacion.query.filter_by(
                id_estudiante=id_estudiante,
                id_materia=id_materia,
                tipo_evaluacion=tipo_evaluacion,
                periodo=periodo,
                anio_academico=anio_academico
            ).first()
            
            if calificacion_existente:
                calificacion_existente.nota = nota
                calificacion_existente.porcentaje = porcentaje
                calificacion_existente.observacion = observacion
                calificacion_existente.registrado_por = usuario_actual.id_usuario
                registros_actualizados += 1
            else:
                nueva_calificacion = Calificacion(
                    id_estudiante=id_estudiante,
                    id_materia=id_materia,
                    tipo_evaluacion=tipo_evaluacion,
                    nota=nota,
                    porcentaje=porcentaje,
                    periodo=periodo,
                    anio_academico=anio_academico,
                    observacion=observacion,
                    registrado_por=usuario_actual.id_usuario
                )
                db.session.add(nueva_calificacion)
                registros_creados += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'{registros_creados} creadas, {registros_actualizados} actualizadas',
            'creados': registros_creados,
            'actualizados': registros_actualizados
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR CALIFICACIONES POR ESTUDIANTE ====================

@calificacion_bp.route('/estudiante/<int:id_estudiante>', methods=['GET'])
@token_required
def obtener_calificaciones_estudiante(usuario_actual, id_estudiante):
    try:
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        es_docente = usuario_actual.tipo_usuario == 'docente'
        es_mismo_estudiante = usuario_actual.estudiante and usuario_actual.estudiante.id_estudiante == id_estudiante
        
        if not (es_admin or es_docente or es_mismo_estudiante):
            return jsonify({'success': False, 'message': 'No tienes permisos'}), 403
        
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404
        
        query = Calificacion.query.filter_by(id_estudiante=id_estudiante)
        
        periodo = request.args.get('periodo')
        anio = request.args.get('anio')
        id_materia = request.args.get('materia')
        
        if periodo:
            query = query.filter_by(periodo=periodo)
        if anio:
            query = query.filter_by(anio_academico=int(anio))
        if id_materia:
            query = query.filter_by(id_materia=int(id_materia))
        
        calificaciones = query.order_by(Calificacion.periodo, Calificacion.id_materia).all()
        
        materias = {}
        for c in calificaciones:
            key = f"{c.id_materia}_{c.periodo}_{c.anio_academico}"
            if key not in materias:
                materias[key] = {
                    'materia': c.materia.to_dict(),
                    'periodo': c.periodo,
                    'notas': [],
                    'suma_ponderada': 0,
                    'ponderacion_total': 0
                }
            valor_ponderado = float(c.nota) * (float(c.porcentaje) / 100)
            materias[key]['notas'].append(c.to_dict())
            materias[key]['suma_ponderada'] += valor_ponderado
            materias[key]['ponderacion_total'] += float(c.porcentaje)
        
        for key, data in materias.items():
            if data['ponderacion_total'] > 0:
                data['promedio'] = round(data['suma_ponderada'], 2)
        
        todos_promedios = [m['promedio'] for m in materias.values() if 'promedio' in m]
        promedio_general = round(sum(todos_promedios) / len(todos_promedios), 2) if todos_promedios else 0
        
        return jsonify({
            'success': True,
            'estudiante': estudiante.to_dict(),
            'promedio_general': promedio_general,
            'materias': list(materias.values()),
            'calificaciones': [c.to_dict() for c in calificaciones]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500


# ==================== CONSULTAR CALIFICACIONES POR GRADO ====================

@calificacion_bp.route('/grado/<int:id_grado>', methods=['GET'])
@token_required
@role_required(['docente', 'administrativo'])
def obtener_calificaciones_grado(usuario_actual, id_grado):
    try:
        periodo = request.args.get('periodo')
        anio = request.args.get('anio')
        id_materia = request.args.get('materia')
        
        if not periodo or not anio:
            return jsonify({'success': False, 'message': 'periodo y anio son requeridos'}), 400
        
        grado = Grado.query.get(id_grado)
        if not grado:
            return jsonify({'success': False, 'message': 'Grado no encontrado'}), 404
        
        estudiantes = Estudiante.query.filter_by(id_grado=id_grado, estado='activo').all()
        
        resultado = []
        suma_promedios = 0
        
        for estudiante in estudiantes:
            query = Calificacion.query.filter_by(
                id_estudiante=estudiante.id_estudiante,
                periodo=periodo,
                anio_academico=int(anio)
            )
            
            if id_materia:
                query = query.filter_by(id_materia=int(id_materia))
            
            calificaciones = query.all()
            
            suma_ponderada = 0
            ponderacion_total = 0
            
            for c in calificaciones:
                suma_ponderada += float(c.nota) * (float(c.porcentaje) / 100)
                ponderacion_total += float(c.porcentaje)
            
            promedio = round(suma_ponderada, 2) if ponderacion_total > 0 else 0
            suma_promedios += promedio
            
            resultado.append({
                'estudiante': estudiante.to_dict(),
                'promedio': promedio,
                'estado': 'Aprobado' if promedio >= 3.0 else 'Reprobado',
                'calificaciones': [c.to_dict() for c in calificaciones]
            })
        
        promedio_grado = round(suma_promedios / len(resultado), 2) if resultado else 0
        aprobados = sum(1 for r in resultado if r['promedio'] >= 3.0)
        
        return jsonify({
            'success': True,
            'grado': grado.to_dict(),
            'periodo': periodo,
            'anio': anio,
            'total_estudiantes': len(resultado),
            'aprobados': aprobados,
            'reprobados': len(resultado) - aprobados,
            'promedio_grado': promedio_grado,
            'estudiantes': resultado
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error: {str(e)}'}), 500