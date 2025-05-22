@echo off

:: Activate venv
call .\venv\Scripts\activate

:: Run Docker db
docker-compose up -d db

:: Run server
uvicorn canellus.asgi:application --host 127.0.0.1 --port 8880 --reload

:: Run server prod mode
@REM uvicorn canellus.asgi:application --host 127.0.0.1 --port 8000 --workers 4

:: Deactivate venv
deactivate

