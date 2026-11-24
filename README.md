# Farmaticas: inventario de medicamentos

Práctica BISOFT-36, cuatrimestre 2026-3. Aplicación web que muestra el inventario disponible de una cadena de farmacias a partir de datos históricos de ventas, que se limpian y se cargan a una base de datos relacional.

Todos los datos son de ejemplo e inventados. No hay información real de clientes.

## Arquitectura

```
Navegador  ->  FastAPI (API + front-end estático, puerto 8000)  ->  PostgreSQL en Supabase (nube)
```

- Front-end: HTML y JavaScript en `web/`, servido por la misma aplicación FastAPI.
- API: FastAPI con los endpoints `GET /inventario` (parámetro opcional `buscar`) y `GET /salud`.
- Base de datos: PostgreSQL con las tablas `drugs`, `customers` y `sales`.
- Inventario disponible = existencias iniciales - unidades vendidas.
- Estado: `Agotado` si el inventario disponible es 0 o menor, `Disponible` en otro caso.

## Requisitos

- Python 3.9 o superior
- Una base de datos PostgreSQL y su cadena de conexión (el proyecto usa Supabase, con el session pooler)

## Instalación

En macOS o Linux:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Editar el archivo `.env` y reemplazar el valor de `DATABASE_URL` por la cadena de conexión real. Ese archivo no se sube al repositorio.

## Datos

El Excel se genera con duplicados y valores nulos a propósito, luego se limpia y se carga a la base de datos:

```
python scripts/generate_excel.py
python scripts/clean_data.py
python scripts/load_to_db.py
```

Archivos que se producen en `data/`:

- `farmaticas_datos_iniciales.xlsx`: datos sin limpiar.
- `farmaticas_datos_limpios.xlsx`: datos limpios.
- `limpieza_log.txt`: métricas de la limpieza.

Reglas de limpieza:

1. Se eliminan las filas de ventas duplicadas exactas.
2. La cantidad nula se recupera como total dividido entre el precio unitario.
3. Los datos nulos de clientes (nombre y ciudad) se reemplazan por `Sin dato`.

Dos medicamentos quedan agotados a propósito, para que la aplicación muestre ambos estados.

## Ejecución

```
source .venv/bin/activate
uvicorn api.main:app
```

Abrir en el navegador:

- `http://127.0.0.1:8000/` aplicación web
- `http://127.0.0.1:8000/docs` documentación interactiva de la API
- `http://127.0.0.1:8000/salud` estado de la conexión con la base de datos

## Pruebas

```
pytest -q
```

Las pruebas de la API usan una base SQLite en memoria, por lo que no dependen de la base en la nube.

## Estructura del proyecto

- `api/`: API FastAPI
- `web/`: front-end
- `db/`: esquema SQL
- `scripts/`: generación, limpieza y carga de datos
- `tests/`: pruebas automáticas
- `data/`: archivos Excel y log de limpieza
