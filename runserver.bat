@echo off

:: Activate venv
call .\venv\Scripts\activate

:: Run server
python manage.py runserver localhost:8000
@REM daphne anki_quiz.asgi:application

:: Deactivate venv
deactivate

