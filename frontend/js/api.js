/**
 * API CLIENT - SGA "NUEVO AMANECER"
 * Maneja todas las comunicaciones con el backend Flask
 */

// Configuración
const API_URL = '/api';
let authToken = localStorage.getItem('access_token');
let refreshToken = localStorage.getItem('refresh_token');

// ==================== FUNCIONES DE AUTENTICACIÓN ====================

/**
 * Guarda los tokens en localStorage
 */
function saveTokens(access, refresh) {
    authToken = access;
    refreshToken = refresh;
    localStorage.setItem('access_token', access);
    localStorage.setItem('refresh_token', refresh);
}

/**
 * Limpia los tokens (cierre de sesión)
 */
function clearTokens() {
    authToken = null;
    refreshToken = null;
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_data');
}

/**
 * Obtiene el usuario actual desde localStorage
 */
function getCurrentUser() {
    const userData = localStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
}

/**
 * Guarda datos del usuario
 */
function saveUserData(userData) {
    localStorage.setItem('user_data', JSON.stringify(userData));
}

// ==================== FUNCIÓN PRINCIPAL FETCH ====================

/**
 * Realiza una petición HTTP al backend
 * @param {string} endpoint - Ruta del endpoint (ej: '/auth/login')
 * @param {object} options - Opciones de fetch (method, body, etc.)
 * @returns {Promise} - Respuesta del servidor
 */
async function apiRequest(endpoint, options = {}) {
    const url = `${API_URL}${endpoint}`;
    
    // Configuración por defecto
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    // Agregar token de autenticación si existe
    if (authToken && !options.noAuth) {
        defaultOptions.headers['Authorization'] = `Bearer ${authToken}`;
    }
    
    // Combinar opciones
    const finalOptions = { ...defaultOptions, ...options };
    
    // Si hay body y es objeto, convertirlo a JSON
    if (finalOptions.body && typeof finalOptions.body === 'object') {
        finalOptions.body = JSON.stringify(finalOptions.body);
    }
    
    try {
        const response = await fetch(url, finalOptions);
        const data = await response.json();
        
        // Si el token expiró (401), intentar refrescar
        if (response.status === 401 && !options._retry) {
            const refreshed = await refreshAccessToken();
            if (refreshed) {
                // Reintentar la petición original con el nuevo token
                options._retry = true;
                return apiRequest(endpoint, options);
            } else {
                // No se pudo refrescar, redirigir a login
                clearTokens();
                window.location.href = 'index.html';
                throw new Error('Sesión expirada');
            }
        }
        
        return { success: response.ok, status: response.status, data };
    } catch (error) {
        console.error('API Error:', error);
        return { success: false, status: 0, data: { message: error.message } };
    }
}

// ==================== REFRESH TOKEN ====================

/**
 * Refresca el access token usando el refresh token
 */
async function refreshAccessToken() {
    if (!refreshToken) return false;
    
    try {
        const response = await fetch(`${API_URL}/auth/refresh`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            saveTokens(data.access_token, data.refresh_token);
            return true;
        }
    } catch (error) {
        console.error('Refresh token error:', error);
    }
    
    return false;
}

// ==================== FUNCIONES DE LOGIN ====================

/**
 * Inicia sesión con email y contraseña
 */
async function login(email, password) {
    const result = await apiRequest('/auth/login', {
        method: 'POST',
        body: { email, password },
        noAuth: true
    });
    
    if (result.success) {
        const { access_token, refresh_token, usuario, dashboard_url } = result.data;
        saveTokens(access_token, refresh_token);
        saveUserData(usuario);
        return { success: true, dashboard_url, usuario };
    }
    
    return { success: false, message: result.data.message };
}

/**
 * Cierra sesión
 */
function logout() {
    clearTokens();
    window.location.href = 'index.html';
}

/**
 * Verifica si el usuario está autenticado
 */
function isAuthenticated() {
    return authToken !== null;
}

// ==================== USUARIOS ====================

/**
 * Obtiene lista de usuarios (solo admin)
 */
async function getUsuarios(filters = {}) {
    const params = new URLSearchParams(filters).toString();
    const result = await apiRequest(`/usuarios/?${params}`);
    return result.success ? result.data.usuarios : [];
}

/**
 * Crea un nuevo usuario (solo admin)
 */
async function crearUsuario(userData) {
    const result = await apiRequest('/usuarios/', {
        method: 'POST',
        body: userData
    });
    return result;
}

/**
 * Actualiza un usuario (solo admin)
 */
async function actualizarUsuario(id, userData) {
    const result = await apiRequest(`/usuarios/${id}`, {
        method: 'PUT',
        body: userData
    });
    return result;
}

/**
 * Elimina un usuario (solo admin)
 */
async function eliminarUsuario(id, hard = false) {
    const result = await apiRequest(`/usuarios/${id}?hard=${hard}`, {
        method: 'DELETE'
    });
    return result;
}

// ==================== CALIFICACIONES ====================

/**
 * Obtiene calificaciones de un estudiante
 */
async function getCalificacionesEstudiante(estudianteId, periodo = null, anio = null) {
    let url = `/calificaciones/estudiante/${estudianteId}`;
    const params = new URLSearchParams();
    if (periodo) params.append('periodo', periodo);
    if (anio) params.append('anio', anio);
    if (params.toString()) url += `?${params.toString()}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Obtiene calificaciones de un grado (docente/admin)
 */
async function getCalificacionesGrado(gradoId, periodo, anio, materiaId = null) {
    let url = `/calificaciones/grado/${gradoId}?periodo=${periodo}&anio=${anio}`;
    if (materiaId) url += `&materia=${materiaId}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Registra una calificación (docente/admin)
 */
async function registrarCalificacion(data) {
    const result = await apiRequest('/calificaciones/', {
        method: 'POST',
        body: data
    });
    return result;
}

/**
 * Registra calificaciones masivas (docente/admin)
 */
async function registrarCalificacionesMasivas(data) {
    const result = await apiRequest('/calificaciones/masiva', {
        method: 'POST',
        body: data
    });
    return result;
}

// ==================== ASISTENCIAS ====================

/**
 * Obtiene asistencias de un estudiante
 */
async function getAsistenciasEstudiante(estudianteId, periodo = null, anio = null) {
    let url = `/asistencias/estudiante/${estudianteId}`;
    const params = new URLSearchParams();
    if (periodo) params.append('periodo', periodo);
    if (anio) params.append('anio', anio);
    if (params.toString()) url += `?${params.toString()}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Obtiene asistencias de un grado por fecha (docente/admin)
 */
async function getAsistenciasGrado(gradoId, fecha, materiaId = null) {
    let url = `/asistencias/grado/${gradoId}?fecha=${fecha}`;
    if (materiaId) url += `&materia=${materiaId}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Registra asistencia individual (docente/admin)
 */
async function registrarAsistencia(data) {
    const result = await apiRequest('/asistencias/', {
        method: 'POST',
        body: data
    });
    return result;
}

/**
 * Registra asistencias masivas (docente/admin)
 */
async function registrarAsistenciasMasivas(data) {
    const result = await apiRequest('/asistencias/masiva', {
        method: 'POST',
        body: data
    });
    return result;
}

/**
 * Justifica una ausencia
 */
async function justificarAusencia(asistenciaId, justificacion, tipo) {
    const result = await apiRequest(`/asistencias/justificar/${asistenciaId}`, {
        method: 'PUT',
        body: { justificacion, tipo_justificacion: tipo }
    });
    return result;
}

// ==================== HORARIOS ====================

/**
 * Obtiene horario de un grado
 */
async function getHorarioGrado(gradoId, periodo = '1', anio = 2026) {
    const result = await apiRequest(`/horarios/grado/${gradoId}?periodo=${periodo}&anio=${anio}`);
    return result.success ? result.data : null;
}

/**
 * Obtiene horario de un docente
 */
async function getHorarioDocente(docenteId, periodo = '1', anio = 2026) {
    const result = await apiRequest(`/horarios/docente/${docenteId}?periodo=${periodo}&anio=${anio}`);
    return result.success ? result.data : null;
}

/**
 * Crea o actualiza un horario (admin)
 */
async function guardarHorario(data) {
    const result = await apiRequest('/horarios/', {
        method: 'POST',
        body: data
    });
    return result;
}

/**
 * Elimina un horario (admin)
 */
async function eliminarHorario(horarioId) {
    const result = await apiRequest(`/horarios/${horarioId}`, {
        method: 'DELETE'
    });
    return result;
}

// ==================== COMUNICACIONES ====================

/**
 * Obtiene mensajes recibidos
 */
async function getMensajesRecibidos(leido = null, limit = 50) {
    let url = `/comunicaciones/recibidos?limit=${limit}`;
    if (leido !== null) url += `&leido=${leido}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Obtiene mensajes enviados
 */
async function getMensajesEnviados(limit = 50) {
    const result = await apiRequest(`/comunicaciones/enviados?limit=${limit}`);
    return result.success ? result.data : null;
}

/**
 * Envía un mensaje
 */
async function enviarMensaje(destinatarioId, asunto, mensaje) {
    const result = await apiRequest('/comunicaciones/', {
        method: 'POST',
        body: { destinatario_id: destinatarioId, asunto, mensaje }
    });
    return result;
}

/**
 * Envía mensaje masivo (docente/admin)
 */
async function enviarMensajeMasivo(data) {
    const result = await apiRequest('/comunicaciones/masivo', {
        method: 'POST',
        body: data
    });
    return result;
}

/**
 * Marca mensaje como leído
 */
async function marcarMensajeLeido(mensajeId) {
    const result = await apiRequest(`/comunicaciones/${mensajeId}/leer`, {
        method: 'PUT'
    });
    return result;
}

/**
 * Elimina un mensaje
 */
async function eliminarMensaje(mensajeId) {
    const result = await apiRequest(`/comunicaciones/${mensajeId}`, {
        method: 'DELETE'
    });
    return result;
}

/**
 * Obtiene detalle de un mensaje
 */
async function getMensaje(mensajeId) {
    const result = await apiRequest(`/comunicaciones/${mensajeId}`);
    return result.success ? result.data : null;
}

// ==================== REPORTES ====================

/**
 * Genera reporte de calificaciones de estudiante
 */
async function getReporteCalificaciones(estudianteId, periodo = null, anio = null, formato = 'json') {
    let url = `/reportes/calificaciones/estudiante/${estudianteId}?formato=${formato}`;
    if (periodo) url += `&periodo=${periodo}`;
    if (anio) url += `&anio=${anio}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Genera reporte de asistencias de estudiante
 */
async function getReporteAsistencias(estudianteId, anio = null, formato = 'json') {
    let url = `/reportes/asistencias/estudiante/${estudianteId}?formato=${formato}`;
    if (anio) url += `&anio=${anio}`;
    
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

/**
 * Genera reporte de rendimiento por grado
 */
async function getReporteRendimientoGrado(gradoId, periodo, anio) {
    const result = await apiRequest(`/reportes/rendimiento/grado/${gradoId}?periodo=${periodo}&anio=${anio}`);
    return result.success ? result.data : null;
}

/**
 * Genera reporte de asistencia por grado (rango de fechas)
 */
async function getReporteAsistenciaGrado(gradoId, fechaInicio, fechaFin) {
    const result = await apiRequest(`/reportes/asistencia/grado/${gradoId}?fecha_inicio=${fechaInicio}&fecha_fin=${fechaFin}`);
    return result.success ? result.data : null;
}

// ==================== ESTADÍSTICAS ====================

/**
 * Obtiene estadísticas de usuarios (admin)
 */
async function getEstadisticasUsuarios() {
    const result = await apiRequest('/usuarios/estadisticas');
    return result.success ? result.data : null;
}

/**
 * Obtiene cantidad de mensajes no leídos
 */
async function getMensajesNoLeidosCount() {
    const result = await apiRequest('/comunicaciones/no-leidos/count');
    return result.success ? result.data.no_leidos : 0;
}

// ==================== UTILIDADES ====================

/**
 * Carga los datos del usuario actual desde el servidor
 */
async function cargarUsuarioActual() {
    const result = await apiRequest('/auth/verify');
    if (result.success) {
        saveUserData(result.data.usuario);
        return result.data.usuario;
    }
    return null;
}
// ==================== HORARIOS (CRUD COMPLETO) ====================

async function getHorarios(filtros = {}) {
    const params = new URLSearchParams(filtros).toString();
    const result = await apiRequest(`/horarios/?${params}`);
    return result.success ? result.data.horarios : [];
}

async function getHorarioPorId(id) {
    const result = await apiRequest(`/horarios/${id}`);
    return result.success ? result.data.horario : null;
}

async function getHorarioGrado(gradoId, periodo = '1', anio = 2026) {
    const result = await apiRequest(`/horarios/grado/${gradoId}?periodo=${periodo}&anio=${anio}`);
    return result.success ? result.data : null;
}

async function getHorarioDocente(docenteId, periodo = '1', anio = 2026) {
    const result = await apiRequest(`/horarios/docente/${docenteId}?periodo=${periodo}&anio=${anio}`);
    return result.success ? result.data : null;
}

async function crearHorario(data) {
    const result = await apiRequest('/horarios/', {
        method: 'POST',
        body: data
    });
    return result;
}

async function actualizarHorario(id, data) {
    const result = await apiRequest(`/horarios/${id}`, {
        method: 'PUT',
        body: data
    });
    return result;
}

async function eliminarHorario(id) {
    const result = await apiRequest(`/horarios/${id}`, {
        method: 'DELETE'
    });
    return result;
}


// ==================== COMUNICACIONES (CRUD COMPLETO) ====================

async function getMensajesRecibidos(leido = null, limit = 50) {
    let url = `/comunicaciones/recibidos?limit=${limit}`;
    if (leido !== null) url += `&leido=${leido}`;
    const result = await apiRequest(url);
    return result.success ? result.data : null;
}

async function getMensajesEnviados(limit = 50) {
    const result = await apiRequest(`/comunicaciones/enviados?limit=${limit}`);
    return result.success ? result.data : null;
}

async function getMensaje(id) {
    const result = await apiRequest(`/comunicaciones/${id}`);
    return result.success ? result.data.mensaje : null;
}

async function enviarMensaje(destinatarioId, asunto, mensaje) {
    const result = await apiRequest('/comunicaciones/', {
        method: 'POST',
        body: { destinatario_id: destinatarioId, asunto, mensaje }
    });
    return result;
}

async function enviarMensajeMasivo(data) {
    const result = await apiRequest('/comunicaciones/masivo', {
        method: 'POST',
        body: data
    });
    return result;
}

async function marcarMensajeLeido(id) {
    const result = await apiRequest(`/comunicaciones/${id}/leer`, {
        method: 'PUT'
    });
    return result;
}

async function actualizarMensaje(id, data) {
    const result = await apiRequest(`/comunicaciones/${id}`, {
        method: 'PUT',
        body: data
    });
    return result;
}

async function eliminarMensaje(id) {
    const result = await apiRequest(`/comunicaciones/${id}`, {
        method: 'DELETE'
    });
    return result;
}

async function getMensajesNoLeidosCount() {
    const result = await apiRequest('/comunicaciones/no-leidos/count');
    return result.success ? result.data.no_leidos : 0;
}

// Exportar funciones para usar en los HTML
/**
 * Lista los grados activos del sistema
 */
async function getGrados() {
    const result = await apiRequest('/grados');
    return result.success ? result.data.grados : [];
}

/**
 * Lista las materias activas del sistema
 */
async function getMaterias() {
    const result = await apiRequest('/materias');
    return result.success ? result.data.materias : [];
}

/**
 * Lista el directorio de contactos (para elegir destinatarios de mensajes)
 */
async function getDirectorio() {
    const result = await apiRequest('/directorio');
    return result.success ? result.data.contactos : [];
}

 window.api = {
    // Auth
    login,
    logout,
    isAuthenticated,
    getCurrentUser,
    cargarUsuarioActual,
    
    // Usuarios
    getUsuarios,
    crearUsuario,
    actualizarUsuario,
    eliminarUsuario,
    getEstadisticasUsuarios,
    
    // Calificaciones
    getCalificacionesEstudiante,
    getCalificacionesGrado,
    registrarCalificacion,
    registrarCalificacionesMasivas,
    eliminarCalificacion,
    actualizarCalificacion,
    
    // Asistencias
    getAsistenciasEstudiante,
    getAsistenciasGrado,
    registrarAsistencia,
    registrarAsistenciasMasivas,
    justificarAusencia,
    eliminarAsistencia,
    
    // Horarios
    getHorarioGrado,
    getHorarioDocente,
    guardarHorario,
    eliminarHorario,
    
    // Comunicaciones
    getMensajesRecibidos,
    getMensajesEnviados,
    enviarMensaje,
    enviarMensajeMasivo,
    marcarMensajeLeido,
    eliminarMensaje,
    getMensaje,
    getMensajesNoLeidosCount,
    
    // Reportes
    getReporteCalificaciones,
    getReporteAsistencias,
    getReporteRendimientoGrado,
    getReporteAsistenciaGrado,

    // Catálogo
    getGrados,
    getMaterias,
    getDirectorio
};
// ==================== ELIMINAR ASISTENCIA ====================
async function eliminarAsistencia(asistenciaId) {
    const result = await apiRequest(`/asistencias/${asistenciaId}`, {
        method: 'DELETE'
    });
    return result;
}

// ==================== ELIMINAR CALIFICACIÓN ====================
async function eliminarCalificacion(calificacionId) {
    const result = await apiRequest(`/calificaciones/${calificacionId}`, {
        method: 'DELETE'
    });
    return result;
}

// ==================== ACTUALIZAR CALIFICACIÓN ====================
async function actualizarCalificacion(calificacionId, data) {
    const result = await apiRequest(`/calificaciones/${calificacionId}`, {
        method: 'PUT',
        body: data
    });
    return result;
}