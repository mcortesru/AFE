@echo off
echo Iniciando Docker...

:: Verifica si Docker Desktop está corriendo
tasklist | find /i "Docker Desktop.exe" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Docker no está en ejecución. Iniciando Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    timeout /t 10
)

:: Esperar hasta que Docker esté completamente iniciado
echo Esperando a que Docker se inicie...
:wait_for_docker
docker info >nul 2>&1
if %ERRORLEVEL% neq 0 (
    timeout /t 5
    goto wait_for_docker
)

echo Docker está en ejecución.

:: Ejecutar el contenedor
echo Iniciando contenedor...
docker run -p 5000:5000 mi_chatbot

:: Abrir navegador
echo Abriendo navegador en http://localhost:5000
start "" "http://localhost:5000"

echo Todo listo! Presiona una tecla para salir.
pause
