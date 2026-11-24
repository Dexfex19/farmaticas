"""Prueba la conexión a PostgreSQL (Supabase) usando DATABASE_URL del archivo .env."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
url = os.getenv("DATABASE_URL")
if not url:
    raise SystemExit("Falta DATABASE_URL en el archivo .env")

engine = create_engine(url)
with engine.connect() as conn:
    version = conn.execute(text("SELECT version()")).scalar()
print("Conexión exitosa:", version)