import os
import django
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from django.core.asgi import get_asgi_application
from starlette.middleware.wsgi import WSGIMiddleware
from fastapi.routing import Mount

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canellus.settings')
django.setup()

# Import FastAPI app
from fastapi_app.api import api_app

# Configure Starlette
from starlette.routing import Mount, Router
from starlette.staticfiles import StaticFiles

# Get the project root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print(BASE_DIR, os.path.join(BASE_DIR, "static"))

# Configure Router
application = Router(
    routes=[
        Mount(
            "/static",
            app=StaticFiles(directory=os.path.join(BASE_DIR, "static"), html=True),  # static route should be first
            name="static",
        ),
        Mount("/api", app=api_app),                    # FastAPI to /api/
        Mount("/", app=get_asgi_application()),        # Django to /
        
    ]
)
