@echo off
chcp 65001 >nul
title Configurar Firewall - Sistema Direccion General

echo ============================================
echo   Configurar Firewall - Puerto 8000
echo ============================================
echo.
echo Este script debe ejecutarse COMO ADMINISTRADOR.
echo Si no lo hiciste, cierralo y usa:
echo   Click derecho ^> Ejecutar como administrador
echo.
pause

echo.
echo [*] Creando regla de firewall para puerto 8000...
netsh advfirewall firewall add rule name="Sistema Gestion (8000)" dir=in action=allow protocol=TCP localport=8000
if %errorlevel% equ 0 (
    echo [OK] Regla creada exitosamente.
) else (
    echo [ERROR] No se pudo crear la regla. Ejecuta como Administrador.
    pause
    exit /b 1
)

echo.
echo [*] Verificando regla...
netsh advfirewall firewall show rule name="Sistema Gestion (8000)" | findstr /i "Rule Name|Local Port|Action"

echo.
echo ============================================
echo   LISTO. Ahora ejecuta iniciar.bat
echo   y prueba desde otro dispositivo:
echo   http://[IP_DEL_SERVIDOR]:8000
echo ============================================
echo.
pause
