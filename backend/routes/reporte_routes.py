"""
RUTAS DE REPORTES - SGA
Endpoints para: Generar reportes en PDF y Excel
"""

from flask import Blueprint, request, jsonify, send_file
from datetime import datetime
import io
import csv
from models import db, Estudiante, Calificacion, Asistencia, Grado, Materia
from auth import token_required, role_required

reporte_bp = Blueprint('reportes', __name__, url_prefix='/api/reportes')


# ==================== REPORTE DE CALIFICACIONES POR ESTUDIANTE ====================

@reporte_bp.route('/calificaciones/estudiante/<int:id_estudiante>', methods=['GET'])
@token_required
def reporte_calificaciones_estudiante(usuario_actual, id_estudiante):
    """
    GET /api/reportes/calificaciones/estudiante/{id_estudiante}
    Genera un reporte JSON con todas las calificaciones de un estudiante
    
    Parámetros query:
    - periodo: 1,2,3,4 (opcional)
    - anio: 2026 (opcional)
    - formato: json (default) o csv
    """
    try:
        # Verificar permisos
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        es_docente = usuario_actual.tipo_usuario == 'docente'
        es_mismo = usuario_actual.estudiante and usuario_actual.estudiante.id_estudiante == id_estudiante
        
        if not (es_admin or es_docente or es_mismo):
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para ver este reporte'
            }), 403
        
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return jsonify({
                'success': False,
                'message': 'Estudiante no encontrado'
            }), 404
        
        periodo = request.args.get('periodo')
        anio = request.args.get('anio', datetime.now().year, type=int)
        
        query = Calificacion.query.filter_by(id_estudiante=id_estudiante, anio_academico=anio)
        if periodo:
            query = query.filter_by(periodo=periodo)
        
        calificaciones = query.all()
        
        # Organizar por materia
        materias = {}
        for c in calificaciones:
            if c.id_materia not in materias:
                materias[c.id_materia] = {
                    'materia': c.materia.nombre,
                    'notas': [],
                    'promedio': 0
                }
            materias[c.id_materia]['notas'].append({
                'tipo': c.tipo_evaluacion,
                'nota': float(c.nota),
                'porcentaje': float(c.porcentaje)
            })
        
        # Calcular promedios
        for m in materias.values():
            suma_ponderada = 0
            for n in m['notas']:
                suma_ponderada += n['nota'] * (n['porcentaje'] / 100)
            m['promedio'] = round(suma_ponderada, 2)
        
        formato = request.args.get('formato', 'json')
        
        if formato == 'csv':
            # Generar CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Materia', 'Tipo Evaluación', 'Nota', 'Porcentaje', 'Valor Ponderado'])
            
            for m in materias.values():
                for n in m['notas']:
                    ponderado = n['nota'] * (n['porcentaje'] / 100)
                    writer.writerow([m['materia'], n['tipo'], n['nota'], n['porcentaje'], round(ponderado, 2)])
            
            # Agregar fila de promedio
            writer.writerow([])
            writer.writerow(['PROMEDIO GENERAL', '', '', '', ''])
            for m in materias.values():
                writer.writerow([m['materia'], 'PROMEDIO', m['promedio'], '100', m['promedio']])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'reporte_calificaciones_{estudiante.usuario.nombre}_{estudiante.usuario.apellido}.csv'
            )
        else:
            return jsonify({
                'success': True,
                'estudiante': estudiante.to_dict(),
                'periodo': periodo or 'Todos',
                'anio': anio,
                'promedio_general': round(sum(m['promedio'] for m in materias.values()) / len(materias), 2) if materias else 0,
                'materias': materias
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }), 500


# ==================== REPORTE DE ASISTENCIAS POR ESTUDIANTE ====================

@reporte_bp.route('/asistencias/estudiante/<int:id_estudiante>', methods=['GET'])
@token_required
def reporte_asistencias_estudiante(usuario_actual, id_estudiante):
    """
    GET /api/reportes/asistencias/estudiante/{id_estudiante}
    Genera un reporte de asistencias de un estudiante
    """
    try:
        es_admin = usuario_actual.tipo_usuario == 'administrativo'
        es_docente = usuario_actual.tipo_usuario == 'docente'
        es_mismo = usuario_actual.estudiante and usuario_actual.estudiante.id_estudiante == id_estudiante
        
        if not (es_admin or es_docente or es_mismo):
            return jsonify({
                'success': False,
                'message': 'No tienes permisos para ver este reporte'
            }), 403
        
        estudiante = Estudiante.query.get(id_estudiante)
        if not estudiante:
            return jsonify({
                'success': False,
                'message': 'Estudiante no encontrado'
            }), 404
        
        anio = request.args.get('anio', datetime.now().year, type=int)
        
        asistencias = Asistencia.query.filter_by(id_estudiante=id_estudiante).filter(
            db.extract('year', Asistencia.fecha) == anio
        ).all()
        
        total = len(asistencias)
        presentes = sum(1 for a in asistencias if a.presente)
        ausentes = total - presentes
        porcentaje = round((presentes / total * 100), 2) if total > 0 else 0
        
        # Agrupar por materia
        por_materia = {}
        for a in asistencias:
            if a.id_materia not in por_materia:
                por_materia[a.id_materia] = {
                    'materia': a.materia.nombre,
                    'total': 0,
                    'presentes': 0
                }
            por_materia[a.id_materia]['total'] += 1
            if a.presente:
                por_materia[a.id_materia]['presentes'] += 1
        
        for m in por_materia.values():
            m['porcentaje'] = round((m['presentes'] / m['total'] * 100), 2) if m['total'] > 0 else 0
        
        formato = request.args.get('formato', 'json')
        
        if formato == 'csv':
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['Fecha', 'Materia', 'Estado', 'Justificación'])
            
            for a in asistencias:
                estado = 'Presente' if a.presente else 'Ausente'
                writer.writerow([a.fecha, a.materia.nombre, estado, a.justificacion or ''])
            
            writer.writerow([])
            writer.writerow(['RESUMEN', '', '', ''])
            writer.writerow(['Total días', total, '', ''])
            writer.writerow(['Presentes', presentes, '', ''])
            writer.writerow(['Ausentes', ausentes, '', ''])
            writer.writerow(['Porcentaje', f'{porcentaje}%', '', ''])
            
            output.seek(0)
            return send_file(
                io.BytesIO(output.getvalue().encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'reporte_asistencias_{estudiante.usuario.nombre}_{estudiante.usuario.apellido}.csv'
            )
        else:
            return jsonify({
                'success': True,
                'estudiante': estudiante.to_dict(),
                'anio': anio,
                'total': total,
                'presentes': presentes,
                'ausentes': ausentes,
                'porcentaje_asistencia': porcentaje,
                'por_materia': por_materia,
                'asistencias_recientes': [a.to_dict() for a in asistencias[-20:]]  # últimas 20
            }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }), 500


# ==================== REPORTE DE RENDIMIENTO POR GRADO ====================

@reporte_bp.route('/rendimiento/grado/<int:id_grado>', methods=['GET'])
@token_required
@role_required(['docente', 'administrativo'])
def reporte_rendimiento_grado(usuario_actual, id_grado):
    """
    GET /api/reportes/rendimiento/grado/{id_grado}
    Genera un reporte de rendimiento académico por grado
    
    Parámetros query:
    - periodo: 1,2,3,4 (requerido)
    - anio: 2026 (requerido)
    """
    try:
        periodo = request.args.get('periodo')
        anio = request.args.get('anio', type=int)
        
        if not periodo or not anio:
            return jsonify({
                'success': False,
                'message': 'periodo y anio son requeridos'
            }), 400
        
        grado = Grado.query.get(id_grado)
        if not grado:
            return jsonify({
                'success': False,
                'message': 'Grado no encontrado'
            }), 404
        
        estudiantes = Estudiante.query.filter_by(id_grado=id_grado, estado='activo').all()
        
        resultados = []
        suma_promedios = 0
        
        for estudiante in estudiantes:
            calificaciones = Calificacion.query.filter_by(
                id_estudiante=estudiante.id_estudiante,
                periodo=periodo,
                anio_academico=anio
            ).all()
            
            # Calcular promedio del estudiante
            suma_ponderada = 0
            ponderacion_total = 0
            
            for c in calificaciones:
                suma_ponderada += float(c.nota) * (float(c.porcentaje) / 100)
                ponderacion_total += float(c.porcentaje)
            
            promedio = round(suma_ponderada, 2) if ponderacion_total > 0 else 0
            suma_promedios += promedio
            
            resultados.append({
                'estudiante': estudiante.to_dict(),
                'promedio': promedio,
                'estado': 'Aprobado' if promedio >= 3.0 else 'Reprobado'
            })
        
        # Ordenar por promedio (mejores primero)
        resultados.sort(key=lambda x: x['promedio'], reverse=True)
        
        promedio_grado = round(suma_promedios / len(resultados), 2) if resultados else 0
        aprobados = sum(1 for r in resultados if r['estado'] == 'Aprobado')
        reprobados = len(resultados) - aprobados
        
        return jsonify({
            'success': True,
            'grado': grado.to_dict(),
            'periodo': periodo,
            'anio': anio,
            'total_estudiantes': len(resultados),
            'aprobados': aprobados,
            'reprobados': reprobados,
            'porcentaje_aprobacion': round((aprobados / len(resultados) * 100), 2) if resultados else 0,
            'promedio_grado': promedio_grado,
            'mejor_promedio': resultados[0]['promedio'] if resultados else 0,
            'peor_promedio': resultados[-1]['promedio'] if resultados else 0,
            'estudiantes': resultados
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }), 500


# ==================== REPORTE DE ASISTENCIA POR GRADO ====================

@reporte_bp.route('/asistencia/grado/<int:id_grado>', methods=['GET'])
@token_required
@role_required(['docente', 'administrativo'])
def reporte_asistencia_grado(usuario_actual, id_grado):
    """
    GET /api/reportes/asistencia/grado/{id_grado}
    Genera un reporte de asistencia por grado
    
    Parámetros query:
    - fecha_inicio: YYYY-MM-DD
    - fecha_fin: YYYY-MM-DD
    """
    try:
        fecha_inicio = request.args.get('fecha_inicio')
        fecha_fin = request.args.get('fecha_fin')
        
        if not fecha_inicio or not fecha_fin:
            return jsonify({
                'success': False,
                'message': 'fecha_inicio y fecha_fin son requeridos'
            }), 400
        
        fecha_inicio_dt = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
        fecha_fin_dt = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        
        grado = Grado.query.get(id_grado)
        if not grado:
            return jsonify({
                'success': False,
                'message': 'Grado no encontrado'
            }), 404
        
        estudiantes = Estudiante.query.filter_by(id_grado=id_grado, estado='activo').all()
        
        resultados = []
        total_asistencias_grado = 0
        total_presentes_grado = 0
        
        for estudiante in estudiantes:
            asistencias = Asistencia.query.filter(
                Asistencia.id_estudiante == estudiante.id_estudiante,
                Asistencia.fecha.between(fecha_inicio_dt, fecha_fin_dt)
            ).all()
            
            total = len(asistencias)
            presentes = sum(1 for a in asistencias if a.presente)
            porcentaje = round((presentes / total * 100), 2) if total > 0 else 0
            
            total_asistencias_grado += total
            total_presentes_grado += presentes
            
            resultados.append({
                'estudiante': estudiante.to_dict(),
                'total_dias': total,
                'presentes': presentes,
                'ausentes': total - presentes,
                'porcentaje': porcentaje,
                'estado': 'Cumple mínimo' if porcentaje >= 80 else 'No cumple mínimo'
            })
        
        # Ordenar por porcentaje (mejores primero)
        resultados.sort(key=lambda x: x['porcentaje'], reverse=True)
        
        promedio_asistencia_grado = round((total_presentes_grado / total_asistencias_grado * 100), 2) if total_asistencias_grado > 0 else 0
        cumplen_minimo = sum(1 for r in resultados if r['porcentaje'] >= 80)
        
        return jsonify({
            'success': True,
            'grado': grado.to_dict(),
            'fecha_inicio': fecha_inicio,
            'fecha_fin': fecha_fin,
            'total_estudiantes': len(resultados),
            'cumplen_minimo': cumplen_minimo,
            'no_cumplen_minimo': len(resultados) - cumplen_minimo,
            'promedio_asistencia_grado': promedio_asistencia_grado,
            'estudiantes': resultados
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al generar reporte: {str(e)}'
        }), 400