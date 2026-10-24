@echo off
setlocal enabledelayedexpansion
title JOEL - Lanzador local
cd /d "%~dp0"

echo ============================================================
echo    JOEL - Lanzador de servicios locales
echo ============================================================
echo.
echo Este lanzador inicia los servicios oficiales de JOEL:
echo   - API web (FastAPI) en http://127.0.0.1:8000
echo   - Servidor local de Minecraft (Paper 1.20.4) en 127.0.0.1:25565
echo   - Bot de Minecraft (node bot.js), si Node.js esta disponible
echo.
echo Solo escucha en 127.0.0.1 (no se expone a Internet).
echo No acepta comandos del usuario: siempre lanza lo mismo.
echo.

if not exist "venv312\Scripts\python.exe" (
    echo [ERROR] No se encontro venv312\Scripts\python.exe
    echo Cree el entorno virtual e instale requirements.txt antes de continuar.
    echo.
    pause
    exit /b 1
)

if not exist "main.py" (
    echo [ERROR] No se encontro main.py en esta carpeta.
    pause
    exit /b 1
)

echo [1/3] Iniciando la API web de JOEL en el puerto 8000...
start "JOEL - API web" cmd /k ""venv312\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000"

echo [2/3] Iniciando el servidor local de Minecraft (Paper 1.20.4)...
where java >nul 2>nul
if %errorlevel%==0 (
    if exist "servidor_minecraft\paper-1.20.4-499.jar" (
        start "JOEL - Servidor Minecraft" /d "%~dp0servidor_minecraft" java -Xms256M -Xmx1024M -XX:+UseG1GC -jar paper-1.20.4-499.jar nogui
    ) else (
        echo [AVISO] No se encontro servidor_minecraft\paper-1.20.4-499.jar. El servidor no se inicio.
    )
) else (
    echo [AVISO] Java no esta en el PATH. El servidor de Minecraft no se inicio.
)

echo [3/3] Comprobando Node.js para el bot de Minecraft...
where node >nul 2>nul
if %errorlevel%==0 (
    if exist "bot.js" (
        start "JOEL - Minecraft" cmd /k "node bot.js"
    ) else (
        echo [AVISO] No se encontro bot.js. El bot de Minecraft no se inicio.
    )
) else (
    echo [AVISO] Node.js no esta en el PATH. El bot de Minecraft no se inicio.
)

echo.
echo JOEL iniciandose.
echo Abra el centro de control en:  http://127.0.0.1:8000
echo.
echo Para detener JOEL, cierre las ventanas "JOEL - API web", "JOEL - Servidor Minecraft" y "JOEL - Minecraft".
echo En la ventana del servidor de Minecraft escriba  stop  para guardar el mundo antes de cerrar.
echo.
pause
