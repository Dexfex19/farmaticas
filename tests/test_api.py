import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("DATABASE_URL", "postgresql://usuario:clave@localhost:5432/prueba")
import api.main as api_main  # noqa: E402


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with engine.begin() as conn:
        conn.exec_driver_sql("CREATE TABLE drugs (drug_id INTEGER PRIMARY KEY, name TEXT, unit_price INTEGER, initial_stock INTEGER)")
        conn.exec_driver_sql("CREATE TABLE sales (sale_id INTEGER PRIMARY KEY, drug_id INTEGER, quantity INTEGER)")
        conn.exec_driver_sql("INSERT INTO drugs VALUES (1, 'Ibuprofeno', 1000, 10), (2, 'Ácido fólico', 500, 5), (3, 'Acetaminofén', 800, 20)")
        conn.exec_driver_sql("INSERT INTO sales VALUES (1, 1, 4), (2, 2, 5)")
    monkeypatch.setattr(api_main, "engine", engine)
    return TestClient(api_main.app)


def test_inventory_sorted_ignoring_accents(client):
    names = [item["nombre"] for item in client.get("/inventario").json()]
    assert names == ["Acetaminofén", "Ácido fólico", "Ibuprofeno"]


def test_inventory_amounts_and_status(client):
    items = {item["nombre"]: item for item in client.get("/inventario").json()}
    assert items["Ibuprofeno"]["inventario_disponible"] == 6
    assert items["Ibuprofeno"]["estado"] == "Disponible"
    assert items["Ácido fólico"]["inventario_disponible"] == 0
    assert items["Ácido fólico"]["estado"] == "Agotado"
    assert items["Acetaminofén"]["unidades_vendidas"] == 0


def test_search_ignores_case_and_accents(client):
    assert [i["nombre"] for i in client.get("/inventario", params={"buscar": "ACIDO"}).json()] == ["Ácido fólico"]
    assert [i["nombre"] for i in client.get("/inventario", params={"buscar": "ibu"}).json()] == ["Ibuprofeno"]
    assert client.get("/inventario", params={"buscar": "zzz"}).json() == []


def test_health_ok(client):
    assert client.get("/salud").json() == {"estado": "ok", "base_de_datos": "conectada"}


def test_health_fails_with_503_when_db_down(client, monkeypatch):
    monkeypatch.setattr(api_main, "engine", create_engine("sqlite:////ruta/que/no/existe/x.db"))
    assert client.get("/salud").status_code == 503


def test_root_serves_front(client):
    assert client.get("/").status_code == 200