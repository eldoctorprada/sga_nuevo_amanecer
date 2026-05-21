@echo off
title SGA Nuevo Amanecer - Servidor Backend
color 0A

echo ========================================
echo   SISTEMA DE GESTION ACADEMICA
echo   "NUEVO AMANECER"
echo ========================================
echo.

cd backend

echo [1/4] Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado
    echo Por favor instala Python desde https://python.org
    pause
    exit /b 1
)
echo [OK] Python encontrado

echo.
echo [2/4] Verificando dependencias...
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando dependencias por primera vez...
    echo Esto puede tomar unos minutos...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Fallo al instalar dependencias
        pause
        exit /b 1
    )
)
echo [OK] Dependencias listas

echo.
echo [3/4] Verificando MySQL...
echo Asegurate que XAMPP este abierto con MySQL encendido
echo.

echo [4/4] Iniciando servidor Flask...
echo.
echo ========================================
echo   🚀 SERVIDOR INICIADO
echo ========================================
echo.
echo   📍 Accede a: http://localhost:5000
echo.
echo   🔐 CREDENCIALES DE PRUEBA:
echo   ----------------------------------------
echo   👨‍💼 Admin:     admin@nuevoamanecer.edu
echo   👨‍🏫 Docente:   docente@nuevoamanecer.edu
echo   🎓 Estudiante: ana.torres@estudiante.edu
echo   ----------------------------------------
echo   🔑 Contraseña para todos: admin123
echo.
echo   ⚠️  Presiona CTRL+C para detener el servidor
echo ========================================
echo.

python app.py

pause