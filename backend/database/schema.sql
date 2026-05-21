-- =====================================================
-- SISTEMA DE GESTIÓN ACADÉMICA "NUEVO AMANECER"
-- BASE DE DATOS: sga_nuevo_amanecer
-- MOTOR: MySQL (InnoDB)
-- FECHA CREACIÓN: Abril 2026
-- =====================================================

-- ==================== CREAR BASE DE DATOS ====================
DROP DATABASE IF EXISTS sga_nuevo_amanecer;
CREATE DATABASE sga_nuevo_amanecer;
USE sga_nuevo_amanecer;

-- ==================== TABLA: USUARIO ====================
-- Clase base abstracta para todos los usuarios del sistema
CREATE TABLE usuario (
    id_usuario INT PRIMARY KEY AUTO_INCREMENT,
    tipo_usuario ENUM('estudiante', 'docente', 'administrativo') NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    apellido VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    telefono VARCHAR(20),
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN DEFAULT TRUE,
    INDEX idx_email (email),
    INDEX idx_tipo_usuario (tipo_usuario)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ==================== TABLA: GRADO ====================
-- Niveles académicos (Primero, Segundo, Tercero, etc.)
CREATE TABLE grado (
    id_grado INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(50) NOT NULL,  -- Ej: "Primero A", "Quinto B"
    nivel TINYINT NOT NULL CHECK (nivel BETWEEN 1 AND 6),
    jornada ENUM('mañana', 'tarde', 'noche') DEFAULT 'mañana',
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: MATERIA ====================
-- Asignaturas del currículo académico
CREATE TABLE materia (
    id_materia INT PRIMARY KEY AUTO_INCREMENT,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(10) NOT NULL UNIQUE,
    horas_semana INT NOT NULL CHECK (horas_semana > 0),
    activo BOOLEAN DEFAULT TRUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: ESTUDIANTE ====================
-- Información específica de estudiantes (hereda de usuario)
CREATE TABLE estudiante (
    id_estudiante INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL UNIQUE,
    documento VARCHAR(20) NOT NULL UNIQUE,
    fecha_nacimiento DATE NOT NULL,
    id_grado INT,
    direccion VARCHAR(200),
    acudiente_nombre VARCHAR(150),
    acudiente_telefono VARCHAR(20),
    estado ENUM('activo', 'inactivo', 'graduado', 'retirado') DEFAULT 'activo',
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_grado) REFERENCES grado(id_grado) ON DELETE SET NULL,
    INDEX idx_documento (documento),
    INDEX idx_estado (estado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: DOCENTE ====================
-- Información específica de docentes (hereda de usuario)
CREATE TABLE docente (
    id_docente INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL UNIQUE,
    especialidad VARCHAR(100),
    codigo_empleado VARCHAR(20) NOT NULL UNIQUE,
    departamento VARCHAR(50),
    titulo_profesional VARCHAR(100),
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    INDEX idx_codigo_empleado (codigo_empleado)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: ADMINISTRATIVO ====================
-- Personal administrativo (hereda de usuario)
CREATE TABLE administrativo (
    id_administrativo INT PRIMARY KEY AUTO_INCREMENT,
    id_usuario INT NOT NULL UNIQUE,
    cargo VARCHAR(50) NOT NULL,
    area VARCHAR(50),
    fecha_ingreso DATE,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: DOCENTE_MATERIA ====================
-- Relación muchos a muchos entre docente y materia
-- Un docente puede dictar varias materias
-- Una materia puede ser dictada por varios docentes
CREATE TABLE docente_materia (
    id_docente_materia INT PRIMARY KEY AUTO_INCREMENT,
    id_docente INT NOT NULL,
    id_materia INT NOT NULL,
    anio_academico INT NOT NULL,
    FOREIGN KEY (id_docente) REFERENCES docente(id_docente) ON DELETE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES materia(id_materia) ON DELETE CASCADE,
    UNIQUE KEY uk_docente_materia_anio (id_docente, id_materia, anio_academico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: HORARIO ====================
-- Distribución semanal de clases
CREATE TABLE horario (
    id_horario INT PRIMARY KEY AUTO_INCREMENT,
    dia_semana ENUM('lunes', 'martes', 'miercoles', 'jueves', 'viernes', 'sabado') NOT NULL,
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    id_grado INT NOT NULL,
    id_materia INT NOT NULL,
    id_docente INT NOT NULL,
    anio_academico INT NOT NULL,
    periodo ENUM('1', '2', '3', '4') NOT NULL,
    aula VARCHAR(20),
    FOREIGN KEY (id_grado) REFERENCES grado(id_grado) ON DELETE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES materia(id_materia) ON DELETE CASCADE,
    FOREIGN KEY (id_docente) REFERENCES docente(id_docente) ON DELETE CASCADE,
    INDEX idx_grado_periodo (id_grado, anio_academico, periodo),
    INDEX idx_docente (id_docente)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: ASISTENCIA ====================
-- Registro diario de asistencia de estudiantes
CREATE TABLE asistencia (
    id_asistencia INT PRIMARY KEY AUTO_INCREMENT,
    id_estudiante INT NOT NULL,
    id_materia INT NOT NULL,
    fecha DATE NOT NULL,
    presente BOOLEAN NOT NULL DEFAULT FALSE,
    justificacion TEXT,
    tipo_justificacion ENUM('enfermedad', 'permiso', 'otro', 'ninguna') DEFAULT 'ninguna',
    registrado_por INT NOT NULL,  -- ID del docente que registró
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES materia(id_materia) ON DELETE CASCADE,
    FOREIGN KEY (registrado_por) REFERENCES usuario(id_usuario),
    UNIQUE KEY uk_asistencia_diaria (id_estudiante, id_materia, fecha),
    INDEX idx_fecha (fecha),
    INDEX idx_estudiante (id_estudiante)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: CALIFICACION ====================
-- Registro de notas por materia, periodo y evaluación
CREATE TABLE calificacion (
    id_calificacion INT PRIMARY KEY AUTO_INCREMENT,
    id_estudiante INT NOT NULL,
    id_materia INT NOT NULL,
    tipo_evaluacion ENUM('parcial1', 'parcial2', 'final', 'trabajo', 'quizz') NOT NULL,
    nota DECIMAL(3,1) NOT NULL CHECK (nota >= 0 AND nota <= 5),
    porcentaje DECIMAL(3,1) NOT NULL CHECK (porcentaje > 0 AND porcentaje <= 100),
    periodo ENUM('1', '2', '3', '4') NOT NULL,
    anio_academico INT NOT NULL,
    observacion TEXT,
    registrado_por INT NOT NULL,
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    FOREIGN KEY (id_materia) REFERENCES materia(id_materia) ON DELETE CASCADE,
    FOREIGN KEY (registrado_por) REFERENCES usuario(id_usuario),
    INDEX idx_estudiante_periodo (id_estudiante, periodo, anio_academico)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: COMUNICACION ====================
-- Mensajería interna del sistema
CREATE TABLE comunicacion (
    id_comunicacion INT PRIMARY KEY AUTO_INCREMENT,
    remitente_id INT NOT NULL,
    destinatario_id INT NOT NULL,
    asunto VARCHAR(200) NOT NULL,
    mensaje TEXT NOT NULL,
    leido BOOLEAN DEFAULT FALSE,
    fecha_envio DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (remitente_id) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (destinatario_id) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    INDEX idx_destinatario_leido (destinatario_id, leido),
    INDEX idx_fecha (fecha_envio)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ==================== TABLA: BITACORA ====================
-- Auditoría de eventos importantes del sistema
CREATE TABLE bitacora (
    id_bitacora INT PRIMARY KEY AUTO_INCREMENT,
    usuario_id INT,
    accion VARCHAR(100) NOT NULL,
    tabla_afectada VARCHAR(50),
    registro_id INT,
    detalles TEXT,
    ip_address VARCHAR(45),
    fecha_evento DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    INDEX idx_fecha (fecha_evento),
    INDEX idx_usuario (usuario_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =====================================================
-- DATOS INICIALES (SEEDERS)
-- =====================================================

-- Insertar grados
INSERT INTO grado (nombre, nivel, jornada) VALUES
('Primero A', 1, 'mañana'),
('Primero B', 1, 'tarde'),
('Segundo A', 2, 'mañana'),
('Segundo B', 2, 'tarde'),
('Tercero A', 3, 'mañana'),
('Tercero B', 3, 'tarde'),
('Cuarto A', 4, 'mañana'),
('Cuarto B', 4, 'tarde'),
('Quinto A', 5, 'mañana'),
('Quinto B', 5, 'tarde');

-- Insertar materias
INSERT INTO materia (nombre, codigo, horas_semana) VALUES
('Matemáticas', 'MAT101', 5),
('Lengua Castellana', 'LEN101', 5),
('Ciencias Naturales', 'CIE101', 4),
('Ciencias Sociales', 'SOC101', 4),
('Inglés', 'ING101', 3),
('Educación Física', 'EDF101', 2),
('Ética y Valores', 'ETI101', 2),
('Tecnología e Informática', 'TEC101', 2),
('Arte y Cultura', 'ART101', 2);

-- Insertar usuarios (contraseñas: todas son 'password123' hasheadas)
-- NOTA: La contraseña 'password123' en bcrypt se generará desde Python
-- Por ahora insertamos los usuarios con una contraseña temporal
INSERT INTO usuario (tipo_usuario, nombre, apellido, email, password_hash, telefono) VALUES
-- Administrador (1)
('administrativo', 'Laura', 'Torres', 'admin@nuevoamanecer.edu', 'temp_password', '3001234567'),
-- Docentes (2-4)
('docente', 'Carlos', 'Martínez', 'docente@nuevoamanecer.edu', 'temp_password', '3101234567'),
('docente', 'Ana', 'García', 'ana.garcia@nuevoamanecer.edu', 'temp_password', '3111234567'),
('docente', 'Juan', 'Pérez', 'juan.perez@nuevoamanecer.edu', 'temp_password', '3121234567'),
-- Estudiantes (5-15)
('estudiante', 'Ana', 'Torres', 'ana.torres@estudiante.edu', 'temp_password', '3201234567'),
('estudiante', 'Carlos', 'Gómez', 'carlos.gomez@estudiante.edu', 'temp_password', '3201234568'),
('estudiante', 'María', 'López', 'maria.lopez@estudiante.edu', 'temp_password', '3201234569'),
('estudiante', 'Pedro', 'Sánchez', 'pedro.sanchez@estudiante.edu', 'temp_password', '3201234570'),
('estudiante', 'Luisa', 'Castro', 'luisa.castro@estudiante.edu', 'temp_password', '3201234571'),
('estudiante', 'Sofía', 'Ramírez', 'sofia.ramirez@estudiante.edu', 'temp_password', '3201234572'),
('estudiante', 'Andrés', 'Díaz', 'andres.diaz@estudiante.edu', 'temp_password', '3201234573'),
('estudiante', 'Valentina', 'Moreno', 'valentina.moreno@estudiante.edu', 'temp_password', '3201234574'),
('estudiante', 'Samuel', 'Rojas', 'samuel.rojas@estudiante.edu', 'temp_password', '3201234575'),
('estudiante', 'Isabella', 'Jiménez', 'isabella.jimenez@estudiante.edu', 'temp_password', '3201234576'),
('estudiante', 'Nicolás', 'Ortiz', 'nicolas.ortiz@estudiante.edu', 'temp_password', '3201234577');

-- Insertar datos específicos de administrativo
INSERT INTO administrativo (id_usuario, cargo, area, fecha_ingreso) VALUES
(1, 'Coordinador Administrativo', 'Administración', '2020-01-15');

-- Insertar datos específicos de docentes
INSERT INTO docente (id_usuario, especialidad, codigo_empleado, departamento) VALUES
(2, 'Matemáticas Puras', 'DOC001', 'Ciencias Exactas'),
(3, 'Literatura', 'DOC002', 'Humanidades'),
(4, 'Educación Física', 'DOC003', 'Bienestar Estudiantil');

-- Insertar datos específicos de estudiantes
INSERT INTO estudiante (id_usuario, documento, fecha_nacimiento, id_grado, acudiente_nombre, acudiente_telefono) VALUES
(5, '1001234567', '2015-03-15', 9, 'María Torres', '3101234567'),
(6, '1001234568', '2015-07-20', 9, 'Andrés Gómez', '3101234568'),
(7, '1001234569', '2014-11-10', 9, 'Fernando López', '3101234569'),
(8, '1001234570', '2015-01-25', 9, 'Carmen Sánchez', '3101234570'),
(9, '1001234571', '2014-09-30', 9, 'Patricia Castro', '3101234571'),
(10, '1001234572', '2015-05-12', 9, 'Roberto Ramírez', '3101234572'),
(11, '1001234573', '2014-12-03', 9, 'Laura Díaz', '3101234573'),
(12, '1001234574', '2015-08-18', 9, 'Jorge Moreno', '3101234574'),
(13, '1001234575', '2014-10-22', 9, 'Claudia Rojas', '3101234575'),
(14, '1001234576', '2015-02-14', 9, 'Luis Jiménez', '3101234576'),
(15, '1001234577', '2015-06-07', 9, 'Daniela Ortiz', '3101234577');

-- Relacionar docentes con materias (docente_materia)
INSERT INTO docente_materia (id_docente, id_materia, anio_academico) VALUES
(1, 1, 2026),  -- Carlos Martínez enseña Matemáticas
(1, 3, 2026),  -- Carlos Martínez enseña Ciencias Naturales
(2, 2, 2026),  -- Ana García enseña Lengua Castellana
(2, 4, 2026),  -- Ana García enseña Sociales
(3, 6, 2026);  -- Juan Pérez enseña Educación Física

-- Insertar horarios de ejemplo
INSERT INTO horario (dia_semana, hora_inicio, hora_fin, id_grado, id_materia, id_docente, anio_academico, periodo, aula) VALUES
('lunes', '08:00:00', '10:00:00', 9, 1, 1, 2026, '1', 'Aula 201'),
('lunes', '10:30:00', '12:30:00', 9, 3, 1, 2026, '1', 'Laboratorio'),
('martes', '08:00:00', '10:00:00', 9, 2, 2, 2026, '1', 'Aula 201'),
('miercoles', '08:00:00', '10:00:00', 9, 1, 1, 2026, '1', 'Aula 201'),
('jueves', '10:30:00', '12:30:00', 9, 4, 2, 2026, '1', 'Aula 201'),
('viernes', '08:00:00', '10:00:00', 9, 6, 3, 2026, '1', 'Cancha');

-- Insertar calificaciones de ejemplo
INSERT INTO calificacion (id_estudiante, id_materia, tipo_evaluacion, nota, porcentaje, periodo, anio_academico, registrado_por, observacion) VALUES
(1, 1, 'parcial1', 4.5, 30, '1', 2026, 2, 'Buen desempeño'),
(1, 1, 'parcial2', 4.0, 30, '1', 2026, 2, 'Mejorar participación'),
(1, 1, 'final', 5.0, 40, '1', 2026, 2, 'Excelente trabajo final'),
(2, 1, 'parcial1', 3.0, 30, '1', 2026, 2, 'Puede mejorar'),
(2, 1, 'parcial2', 3.5, 30, '1', 2026, 2, ''),
(2, 1, 'final', 3.0, 40, '1', 2026, 2, '');

-- Insertar asistencias de ejemplo
INSERT INTO asistencia (id_estudiante, id_materia, fecha, presente, registrado_por) VALUES
(1, 1, '2026-03-15', TRUE, 2),
(2, 1, '2026-03-15', FALSE, 2),
(3, 1, '2026-03-15', TRUE, 2),
(4, 1, '2026-03-15', TRUE, 2),
(5, 1, '2026-03-15', FALSE, 2);

-- =====================================================
-- VISTAS ÚTILES
-- =====================================================

-- Vista: Promedio de estudiantes por materia
CREATE VIEW v_promedios_estudiantes AS
SELECT 
    e.id_estudiante,
    CONCAT(u.nombre, ' ', u.apellido) AS nombre_completo,
    m.nombre AS materia,
    c.periodo,
    c.anio_academico,
    ROUND(AVG(c.nota), 2) AS promedio
FROM calificacion c
JOIN estudiante e ON c.id_estudiante = e.id_estudiante
JOIN usuario u ON e.id_usuario = u.id_usuario
JOIN materia m ON c.id_materia = m.id_materia
GROUP BY e.id_estudiante, m.id_materia, c.periodo, c.anio_academico;

-- Vista: Porcentaje de asistencia por estudiante
CREATE VIEW v_asistencia_estudiantes AS
SELECT 
    e.id_estudiante,
    CONCAT(u.nombre, ' ', u.apellido) AS nombre_completo,
    COUNT(*) AS total_dias,
    SUM(CASE WHEN a.presente = TRUE THEN 1 ELSE 0 END) AS dias_presentes,
    ROUND(SUM(CASE WHEN a.presente = TRUE THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS porcentaje_asistencia
FROM asistencia a
JOIN estudiante e ON a.id_estudiante = e.id_estudiante
JOIN usuario u ON e.id_usuario = u.id_usuario
GROUP BY e.id_estudiante;

-- =====================================================
-- PROCEDIMIENTOS ALMACENADOS
-- =====================================================

-- Procedimiento: Calcular promedio final de un estudiante por período
DELIMITER //
CREATE PROCEDURE sp_calcular_promedio_periodo(
    IN p_id_estudiante INT,
    IN p_periodo VARCHAR(2),
    IN p_anio INT
)
BEGIN
    SELECT 
        m.nombre AS materia,
        SUM(c.nota * c.porcentaje / 100) AS promedio_periodo,
        CASE 
            WHEN SUM(c.nota * c.porcentaje / 100) >= 4.6 THEN 'Excelente'
            WHEN SUM(c.nota * c.porcentaje / 100) >= 4.0 THEN 'Muy Bien'
            WHEN SUM(c.nota * c.porcentaje / 100) >= 3.0 THEN 'Aprobado'
            ELSE 'Reprobado'
        END AS estado
    FROM calificacion c
    JOIN materia m ON c.id_materia = m.id_materia
    WHERE c.id_estudiante = p_id_estudiante
        AND c.periodo = p_periodo
        AND c.anio_academico = p_anio
    GROUP BY m.id_materia;
END //
DELIMITER ;

-- =====================================================
-- TRIGGERS
-- =====================================================

-- Trigger: Registrar en bitácora cuando se inserta una calificación
DELIMITER //
CREATE TRIGGER tr_bitacora_calificacion_insert
AFTER INSERT ON calificacion
FOR EACH ROW
BEGIN
    INSERT INTO bitacora (usuario_id, accion, tabla_afectada, registro_id, detalles)
    VALUES (NEW.registrado_por, 'INSERT', 'calificacion', NEW.id_calificacion, 
            CONCAT('Nota ', NEW.nota, ' en materia ', NEW.id_materia, ' para estudiante ', NEW.id_estudiante));
END //
DELIMITER ;

-- =====================================================
-- AJUSTES DE CREDENCIALES DE PRUEBA
-- =====================================================
UPDATE grado SET jornada = 'ma?ana' WHERE jornada = 'ma??ana';
UPDATE usuario SET password_hash = '$2b$12$6NQukTYtNLVXk7qUtrxzduAUKhfypCjzYZ6KA3GrF7pJfL4ZmkJQm' WHERE email = 'admin@nuevoamanecer.edu';
UPDATE usuario SET password_hash = '$2b$12$sdEF3hAr5aFVMOQ1FeMV.OdQBMW3R2jwBYM4.fqF8Bhn26gyrtjXO' WHERE tipo_usuario = 'docente';
UPDATE usuario SET password_hash = '$2b$12$qYQLPxYc/fi20xVPNl759uiWNzXoKLNSsWBWQvW1u.2oOj2bquhoG' WHERE tipo_usuario = 'estudiante';

-- =====================================================
-- FIN DEL SCRIPT
-- =====================================================