import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/db")

def obtener_conexion():
    """Conecta con la base de datos local de PostgreSQL 12.4-1."""
    try:
        conexion = psycopg2.connect(
            DATABASE_URL,
            client_encoding='utf8'
        )
        return conexion
    except Exception as e:
        print(f"Error de conexión a PostgreSQL local: {e}")
        raise e