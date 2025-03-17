import os
import time
import subprocess
import traceback
import requests
import webbrowser

import sys
print(f"Versión de Python: {sys.version}")



DOCKER_DESKTOP_PATH = r"C:\Program Files\Docker\Docker\Docker Desktop.exe"
PROJECT_DIR = r"C:\apppython\AFE"
APP_URL = "http://127.0.0.1:5000"

def log_error(message):
    """Guarda errores en un archivo de texto."""
    with open("error_log.txt", "a") as f:
        f.write(message + "\n")

def is_docker_ready():
    """Verifica si Docker está funcionando ejecutando `docker info`."""
    try:
        subprocess.run(["docker", "info"], stdout=subprocess.PIPE,
stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        return False

def start_docker():
    """Inicia Docker Desktop si no está corriendo."""
    print("Verificando si Docker está en ejecución...")
    if not is_docker_ready():
        print("Iniciando Docker Desktop...")
        os.startfile(DOCKER_DESKTOP_PATH)

        for i in range(30):
            if is_docker_ready():
                print("✅ Docker está listo.")
                break
            print(f"⌛ Esperando a que Docker arranque... ({i+1}/30)")
            time.sleep(10)
        else:
            log_error("Docker no se inició a tiempo.")
            print("❌ Docker no se inició en 5 minutos.")
            return
    else:
        print("✅ Docker ya estaba en ejecución.")

def start_docker_compose():
    """Ejecuta `docker compose up` en el directorio del proyecto."""
    print("🚀 Ejecutando `docker compose up`...")
    try:
        subprocess.run(["docker", "compose", "up"], cwd=PROJECT_DIR,
shell=True, check=True)
        print("✅ Docker Compose iniciado correctamente.")
    except subprocess.CalledProcessError as e:
        log_error(f"Error ejecutando Docker Compose: {str(e)}")
        print("❌ Error en Docker Compose. Revisa error_log.txt.")

def wait_for_app():
    """Espera hasta que la aplicación en localhost:5000 esté disponible."""
    print("⌛ Esperando a que la aplicación esté disponible en localhost:5000...")

    for i in range(30):  # Espera hasta 5 minutos
        try:
            response = requests.get(APP_URL, timeout=2)
            if response.status_code == 200:
                print("✅ Aplicación disponible.")
                return True
        except requests.RequestException:
            pass
        print(f"⌛ Intento {i+1}: La aplicación aún no responde...")
        time.sleep(10)

    print("❌ La aplicación no respondió en 5 minutos.")
    return False

def open_browser():
    """Abre el navegador en localhost:5000."""
    print("🌍 Abriendo el navegador en localhost:5000...")
    webbrowser.open(APP_URL)

if __name__ == "__main__":
    try:
        start_docker()
        start_docker_compose()
        if wait_for_app():
            open_browser()
    except Exception as e:
        log_error(traceback.format_exc())
        print("❌ Error inesperado. Revisa error_log.txt.")

input("Presiona Enter para salir...")