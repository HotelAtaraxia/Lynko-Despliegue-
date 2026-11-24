#!/usr/bin/env bash
# Salir inmediatamente si ocurre algún error
set -o errexit

# 1. Instalar las dependencias
pip install --upgrade pip
pip install -r requirements.txt

# 2. (Opcional) Si manejas migraciones con Alembic para PostgreSQL:
# alembic upgrade head

uvicorn app:app --reload



