@echo off
cd ..\AFE
call mi_entorno_virtual\Scripts\activate
cd web
start /B python app.py
timeout /t 5
start http://127.0.0.1:5000/
