#!/bin/bash
# Azure App Service custom startup script
gunicorn --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind=0.0.0.0:${PORT:-8000} --timeout 600 src.api:app
