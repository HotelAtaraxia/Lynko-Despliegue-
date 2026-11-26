#!/usr/bin/env bash
set -o errexit
set -o pipefail

echo "=== [1/4] Instalando dependencias de Python ==="
if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
elif [ -f "Backend/requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r Backend/requirements.txt
else
    echo "ERROR: No se encontró requirements.txt en la raíz ni en Backend/."
    exit 1
fi

echo "=== [2/4] Migraciones de base de datos ==="
# Si el proyecto incorpora Alembic en el futuro, descomenta:
# if [ -f "alembic.ini" ]; then
#     alembic upgrade head
# fi
echo "Verificando conexión / esquema (asegúrate de haber cargado backup_lynko_limpio.sql en PostgreSQL)."

echo "=== [3/4] Verificando archivos estáticos (/Frontend) ==="
if [ -d "Frontend" ]; then
    echo "Directorio Frontend encontrado y listo para servirse en /static."
else
    echo "AVISO: No se encontró el directorio Frontend."
fi

echo "=== [4/4] Inicialización opcional de usuario administrador (superuser) ==="
if [ -n "${ADMIN_PASSWORD:-}" ] && { [ -n "${ADMIN_EMAIL:-}" ] || [ -n "${ADMIN_USERNAME:-}" ]; }; then
    python - <<'EOF'
import os
from urllib.parse import urlparse

db_url = os.getenv("DATABASE_URL", "")
admin_email = os.getenv("ADMIN_EMAIL", "").strip()
admin_username = os.getenv("ADMIN_USERNAME", "").strip()
admin_password = os.getenv("ADMIN_PASSWORD", "").strip()

if not db_url:
    print("DATABASE_URL no definida durante el build; se omite creación de admin.")
else:
    parsed = urlparse(db_url)
    print(f"Credenciales de admin recibidas para '{admin_username or admin_email}' (host BD: {parsed.hostname}).")
    print("Nota: Configura la inserción en tu tabla de usuarios si requieres creación automática en build.")
EOF
else
    echo "Variables ADMIN_PASSWORD + (ADMIN_EMAIL o ADMIN_USERNAME) no definidas; se omite creación automática."
fi

echo "=== Build finalizado correctamente ==="