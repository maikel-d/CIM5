@echo off
echo ========================================
echo Instalando tarea programada: Limpieza Semanal
echo ========================================
echo.
set SCRIPT_DIR=%~dp0
set SCRIPT_DIR=%SCRIPT_DIR:~0,-1%
echo Directorio: %SCRIPT_DIR%
echo.
schtasks /Create /SC WEEKLY /D SUN /TN "DireccionGeneral\LimpiezaSemanal" /TR ""%SCRIPT_DIR%\limpiar_semanal.bat"" /ST 03:00 /F
echo.
if %ERRORLEVEL% EQU 0 (
    echo [OK] Tarea programada instalada correctamente.
    echo Se ejecutara cada domingo a las 3:00 AM
) else (
    echo [ERROR] No se pudo instalar la tarea.
    echo Ejecuta este script como Administrador.
)
echo.
pause
