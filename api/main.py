"""API de inventario de Farmaticas. Sirve también el front-end de la carpeta web/."""

import os
import unicodedata
from pathlib import Path
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Falta DATABASE_URL en el archivo .env")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
WEB_DIR = Path(__file__).resolve().parent.parent / "web"

# Los alias en español son el contrato público de la API
INVENTORY_QUERY = text("""
    SELECT d.drug_id AS id_medicamento,
           d.name AS nombre,
           d.unit_price AS precio_unitario,
           d.initial_stock AS existencias_iniciales,
           COALESCE(SUM(s.quantity), 0) AS unidades_vendidas,
           d.initial_stock - COALESCE(SUM(s.quantity), 0) AS inventario_disponible
    FROM drugs d
    LEFT JOIN sales s ON s.drug_id = d.drug_id
    GROUP BY d.drug_id, d.name, d.unit_price, d.initial_stock
""")


class InventoryItem(BaseModel):
    id_medicamento: int
    nombre: str
    precio_unitario: int
    existencias_iniciales: int
    unidades_vendidas: int
    inventario_disponible: int
    estado: Literal["Disponible", "Agotado"]


def normalize(value):
    """Minúsculas y sin tildes: busca y ordena igual sin depender de la colación de la base."""
    decomposed = unicodedata.normalize("NFD", value)
    return "".join(c for c in decomposed if unicodedata.category(c) != "Mn").lower()


def stock_status(available):
    return "Agotado" if available <= 0 else "Disponible"


app = FastAPI(title="API de Inventario Farmaticas")


@app.get("/salud")
def health():
    """Comprueba que la API llega a la base de datos."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="No se pudo conectar a la base de datos")
    return {"estado": "ok", "base_de_datos": "conectada"}


@app.get("/inventario", response_model=List[InventoryItem])
def get_inventory(buscar: Optional[str] = Query(None, description="Texto a buscar en el nombre del medicamento")):
    """Inventario disponible = existencias iniciales - unidades vendidas. Ordenado por nombre."""
    try:
        with engine.connect() as conn:
            rows = conn.execute(INVENTORY_QUERY).mappings().all()
    except SQLAlchemyError:
        raise HTTPException(status_code=503, detail="No se pudo consultar la base de datos")

    items = [dict(row, estado=stock_status(row["inventario_disponible"])) for row in rows]
    if buscar:
        needle = normalize(buscar)
        items = [item for item in items if needle in normalize(item["nombre"])]
    return sorted(items, key=lambda item: normalize(item["nombre"]))


# Debe ir al final: sirve el front y no debe tapar las rutas de la API
app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")