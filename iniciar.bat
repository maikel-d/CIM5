@echo off
chcp 65001 >nul
title Sistema de Gestion - Direccion General
echo ============================================
echo   Sistema de Gestion - Direccion General
echo ============================================
echo.

:: Activar entorno virtual
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo [OK] Entorno virtual activado
) else (
    echo [*] Usando Python del sistema
)

echo.
echo [*] Ejecutando migraciones...
python manage.py migrate 2>nul
echo [OK] Migraciones aplicadas

echo.
echo [*] Verificando superusuario...
python setup_admin.py 2>nul

:: Detectar IP local (via Python, mas confiable)
setlocal enabledelayedexpansion
set "IP="
for /f "tokens=*" %%i in ('python detectar_ip.py 2^>nul') do set "IP=%%i"

cls
echo ============================================
echo   Sistema de Gestion - Direccion General
echo ============================================
echo.
echo [OK] Entorno virtual activado
echo [OK] Migraciones aplicadas
echo [OK] Superusuario verificado
echo.
echo ============================================
echo   http://127.0.0.1:8000  -  Esta computadora
if defined IP (
    echo   http://!IP!:8000      -  Red local
)
echo.
echo   Las credenciales del superusuario se
echo   mostraron al ejecutar la configuracion.
echo.
echo   Si olvidaste la contrasena, ejecuta:
echo   python manage.py changepassword admin
echo ============================================

echo.
python manage.py runserver 0.0.0.0:8000

pause
