# Sistema de Gestión Académica (SGA) — "Nuevo Amanecer"

Sistema web para la gestión académica de una institución educativa: administra
usuarios (administrativos, docentes y estudiantes), grados, materias,
calificaciones, asistencias, horarios y comunicaciones internas.

Proyecto desarrollado como evidencia del programa **Tecnología en Análisis y
Desarrollo de Software (ADSI)** del SENA — Ficha 3186626.

---

## Tabla de contenido

1. [Tecnologías utilizadas](#tecnologías-utilizadas)
2. [Requisitos previos](#requisitos-previos)
3. [Instalación local (paso a paso)](#instalación-local-paso-a-paso)
4. [Credenciales de prueba](#credenciales-de-prueba)
5. [Despliegue en la nube (Railway)](#despliegue-en-la-nube-railway)
6. [Estructura del proyecto](#estructura-del-proyecto)
7. [Autor](#autor)

---

## Tecnologías utilizadas

| Componente             | Tecnología                                   |
|------------------------|----------------------------------------------|
| Lenguaje backend       | Python 3.11                                  |
| Framework web          | Flask                                        |
| ORM (base de datos)    | SQLAlchemy (Flask-SQLAlchemy)                |
| Base de datos          | MySQL 8                                       |
| Autenticación          | JWT (PyJWT) + bcrypt                          |
| Servidor de producción | Gunicorn                                      |
| Frontend               | HTML5, CSS3, JavaScript (vanilla)            |
| Plataforma de despliegue | Railway (hosting gratuito en la nube)      |

---

## Requisitos previos

Antes de instalar, asegúrate de tener en tu equipo:

- **Python 3.11** o superior — [https://www.python.org/downloads/](https://www.python.org/downloads/)
- **MySQL 8** o **XAMPP** (que incluye MySQL) — [https://www.apachefriends.org/](https://www.apachefriends.org/)
- **Git** — [https://git-scm.com/downloads](https://git-scm.com/downloads)
- Un navegador web (Chrome, Edge, Firefox, etc.)

---

## Instalación local (paso a paso)

### 1. Clonar el repositorio

Abre una terminal (CMD o PowerShell en Windows) y ejecuta:

```bash
git clone https://github.com/eldoctorprada/sga_nuevo_amanecer.git
cd sga_nuevo_amanecer
```

### 2. Crear y activar un entorno virtual

```bash
python -m venv venv
```

Activarlo en **Windows**:

```bash
venv\Scripts\activate
```

O en **Linux / macOS**:

```bash
source venv/bin/activate
```

### 3. Instalar las dependencias

```bash
pip install -r requirements.txt
```

Esto instala Flask, SQLAlchemy, PyMySQL, bcrypt, PyJWT, Gunicorn y demás librerías.

### 4. Configurar la base de datos

1. Inicia tu servidor MySQL (o abre XAMPP y enciende el módulo **MySQL**).
2. Crea una base de datos llamada `sga_nuevo_amanecer`.
3. Carga la estructura y los datos de prueba. Tienes **dos opciones**:
   - **Opción A — automática (recomendada):** la aplicación crea las tablas y
     carga los usuarios de prueba por sí sola la primera vez que arranca.
   - **Opción B — manual:** importa el archivo
     `backend/database/schema.sql` desde phpMyAdmin o por consola:
     ```bash
     mysql -u root -p sga_nuevo_amanecer < backend/database/schema.sql
     ```

> **Nota sobre la conexión:** por defecto, el archivo `backend/config.py` se
> conecta a `mysql+pymysql://root:@127.0.0.1:3306/sga_nuevo_amanecer`
> (usuario `root` sin contraseña). Si tu MySQL usa otra contraseña o puerto,
> ajusta ese valor o define la variable de entorno `DATABASE_URL`.

### 5. Ejecutar la aplicación

```bash
cd backend
python app.py
```

Si todo está correcto, verás en la consola un mensaje similar a:

```
Servidor corriendo en: http://localhost:5000
```

### 6. Abrir la aplicación en el navegador

Ingresa a:

```
http://localhost:5000
```

Verás la pantalla de inicio de sesión del sistema.

---

## Credenciales de prueba

Usa cualquiera de estos usuarios para ingresar y probar los distintos roles:

| Rol         | Correo                          | Contraseña      |
|-------------|---------------------------------|-----------------|
| Administrador | `admin@nuevoamanecer.edu`     | `admin123`      |
| Docente     | `docente@nuevoamanecer.edu`     | `docente123`    |
| Estudiante  | `ana.torres@estudiante.edu`     | `estudiante123` |

---

## Despliegue en la nube (Railway)

La aplicación está desplegada en **Railway**, una plataforma de hosting con
plan gratuito. El despliegue en la nube permite acceder al sistema desde
cualquier navegador sin instalar nada localmente.

### Archivos clave para el despliegue

- **`Procfile`** (en la raíz): indica a Railway cómo arrancar la aplicación.
  ```
  web: cd backend && gunicorn --bind 0.0.0.0:${PORT:-5000} --timeout 120 wsgi:app
  ```
- **`requirements.txt`** (en la raíz): lista de dependencias que Railway instala.
- **`backend/wsgi.py`**: punto de entrada que usa Gunicorn en producción.

### Variable de entorno requerida

Railway inyecta la conexión a su base de datos MySQL mediante la variable
**`DATABASE_URL`**, configurada con el formato:

```
mysql+pymysql://<usuario>:<contraseña>@<host>:<puerto>/<base_de_datos>
```

> El prefijo `mysql+pymysql://` es indispensable: es el controlador que usa la
> aplicación para conectarse a MySQL. La aplicación también convierte
> automáticamente una URL que llegue como `mysql://` al formato correcto.

### Inicialización automática

Al arrancar en Railway, la aplicación:

1. Se conecta a la base de datos MySQL de Railway.
2. Crea todas las tablas si no existen.
3. Carga los usuarios de prueba y los datos iniciales.

De esta forma, el sistema queda listo para usarse inmediatamente después del
despliegue, sin pasos manuales adicionales.

---

## Estructura del proyecto

```
sga_nuevo_amanecer/
├── Procfile                 # Configuración de arranque para Railway
├── requirements.txt         # Dependencias de Python
├── backend/
│   ├── app.py               # Aplicación Flask (factory + auto-setup de BD)
│   ├── wsgi.py              # Punto de entrada para Gunicorn (producción)
│   ├── config.py           # Configuración (conexión a BD, JWT, etc.)
│   ├── models.py           # Modelos de datos (tablas) con SQLAlchemy
│   ├── auth.py             # Autenticación: JWT y hash de contraseñas
│   ├── routes/             # Rutas de la API (blueprints)
│   └── database/
│       └── schema.sql      # Script SQL de la base de datos
└── frontend/
    ├── index.html          # Pantalla de inicio de sesión
    ├── dashboard*.html     # Paneles por rol
    ├── css/                # Estilos
    └── js/
        └── api.js          # Cliente que consume la API del backend
```

---

## Autor

**Fredy Acosta** — Aprendiz SENA
Tecnología en Análisis y Desarrollo de Software (ADSI) — Ficha 3186626
Repositorio: [github.com/eldoctorprada/sga_nuevo_amanecer](https://github.com/eldoctorprada/sga_nuevo_amanecer)
