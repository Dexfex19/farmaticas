"""Crea las tablas en PostgreSQL (Supabase) y carga los datos limpios."""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

import clean_data as clean

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "db" / "schema.sql"
TABLES = ("drugs", "customers", "sales")  # orden por llaves foráneas

NEGATIVE_STOCK_QUERY = """
SELECT COUNT(*) FROM (
    SELECT d.drug_id
    FROM drugs d
    LEFT JOIN sales s ON s.drug_id = d.drug_id
    GROUP BY d.drug_id, d.initial_stock
    HAVING d.initial_stock - COALESCE(SUM(s.quantity), 0) < 0
) t
"""


def main():
    load_dotenv()
    url = os.getenv("DATABASE_URL")
    if not url:
        raise SystemExit("Falta DATABASE_URL en el archivo .env")

    drugs, customers, sales = clean.read_raw(clean.OUTPUT_PATH)
    sales["date"] = sales["date"].dt.date
    frames = {"drugs": drugs, "customers": customers, "sales": sales}

    engine = create_engine(url)
    # Una sola transacción: si algo falla, no queda nada a medias
    with engine.begin() as conn:
        conn.exec_driver_sql(SCHEMA_PATH.read_text(encoding="utf-8"))
        for name in TABLES:
            frames[name].to_sql(name, conn, if_exists="append", index=False, method="multi", chunksize=500)
        counts = {name: conn.execute(text(f"SELECT COUNT(*) FROM {name}")).scalar() for name in TABLES}
        negatives = conn.execute(text(NEGATIVE_STOCK_QUERY)).scalar()

    print("Filas en la base:", ", ".join(f"{name}={n}" for name, n in counts.items()))
    print(f"Medicamentos con inventario negativo en la base: {negatives}")


if __name__ == "__main__":
    main()