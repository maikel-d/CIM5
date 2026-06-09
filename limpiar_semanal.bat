@echo off
REM ========================================
REM Limpieza Semanal de Archivos Huerfanos
REM Direccion General - Sistema de Gestion
REM Programada via Windows Task Scheduler
REM ========================================

cd /d %%~dp0
set LOG_FILE=%%~dp0logs\limpieza_%%DATE:~-4%%%%DATE:~3,2%%%%DATE:~0,2%%.log

if not exist %%~dp0logs mkdir %%~dp0logs

echo [%%DATE%% %%TIME%%] Iniciando limpieza de archivos huerfanos... >> %%LOG_FILE%%

"venv\Scripts\python.exe" manage.py limpiar_archivos_huerfanos --eliminar >> %%LOG_FILE%% 2>&1

echo [%%DATE%% %%TIME%%] Limpieza completada. >> %%LOG_FILE%%
echo ======================================== >> %%LOG_FILE%%
