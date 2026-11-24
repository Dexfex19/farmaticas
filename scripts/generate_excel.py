"""Genera el Excel de ejemplo de Farmaticas con datos inventados."""

import random
from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font

# --- Parámetros: cambiarlos solo aquí ---
SEED = 42
N_DRUGS = 30
N_CUSTOMERS = 200
N_SALES = 1500
START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 10, 31)
STOCK_MIN = 20  # margen mínimo de stock por encima de lo vendido
STOCK_MAX = 200  # margen máximo de stock por encima de lo vendido
MAX_QUANTITY = 3
NULL_RATE = 0.05
DUPLICATE_RATE = 0.05
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "farmaticas_datos_iniciales.xlsx"

# Nombres visibles en el Excel. El código interno sigue en inglés.
SHEET_NAMES = {"drugs": "Medicamentos", "customers": "Clientes", "sales": "Ventas"}
COLUMN_NAMES = {
    "drugs": {
        "drug_id": "ID Medicamento",
        "name": "Nombre",
        "unit_price": "Precio unitario (₡)",
        "initial_stock": "Existencias iniciales",
    },
    "customers": {
        "customer_id": "ID Cliente",
        "full_name": "Nombre completo",
        "city": "Ciudad",
    },
    "sales": {
        "sale_id": "ID Venta",
        "date": "Fecha",
        "customer_id": "ID Cliente",
        "drug_id": "ID Medicamento",
        "quantity": "Cantidad",
        "total": "Total (₡)",
    },
}

DRUG_NAMES = [
    "Acetaminofén", "Ibuprofeno", "Amoxicilina", "Omeprazol", "Loratadina",
    "Cetirizina", "Diclofenaco", "Naproxeno", "Metformina", "Losartán",
    "Enalapril", "Atorvastatina", "Salbutamol", "Dexametasona", "Famotidina",
    "Azitromicina", "Ciprofloxacino", "Metronidazol", "Clorfenamina", "Complejo B",
    "Vitamina C", "Sales de rehidratación", "Hierro", "Ácido fólico", "Simeticona",
    "Loperamida", "Bromhexina", "Guaifenesina", "Clotrimazol", "Ketoconazol",
]
FIRST_NAMES = ["María", "José", "Ana", "Luis", "Carlos", "Sofía", "Javier", "Daniela", "Andrés", "Valeria"]
LAST_NAMES = ["Rojas", "Mora", "Vargas", "Jiménez", "Solís", "Castro", "Quesada", "Ramírez", "Araya", "Chaves"]
CITIES = ["San José", "Cartago", "Heredia", "Alajuela", "Limón", "Puntarenas", "Liberia"]


def make_drugs(rng):
    """Medicamentos con precio en colones. El stock inicial se calcula después, con las ventas."""
    rows = []
    for drug_id, name in enumerate(DRUG_NAMES[:N_DRUGS], start=1):
        rows.append({
            "drug_id": drug_id,
            "name": name,
            "unit_price": rng.randrange(500, 15000, 50),
        })
    return pd.DataFrame(rows)


def make_customers(rng):
    rows = []
    for customer_id in range(1, N_CUSTOMERS + 1):
        full_name = f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)} {rng.choice(LAST_NAMES)}"
        rows.append({
            "customer_id": customer_id,
            "full_name": full_name,
            "city": rng.choice(CITIES),
        })
    return pd.DataFrame(rows)


def make_sales(rng, drugs):
    days = (END_DATE - START_DATE).days
    prices = dict(zip(drugs["drug_id"], drugs["unit_price"]))
    rows = []
    for sale_id in range(1, N_SALES + 1):
        drug_id = rng.randint(1, N_DRUGS)
        quantity = rng.randint(1, MAX_QUANTITY)
        rows.append({
            "sale_id": sale_id,
            "date": (START_DATE + timedelta(days=rng.randint(0, days))).date(),
            "customer_id": rng.randint(1, N_CUSTOMERS),
            "drug_id": drug_id,
            "quantity": quantity,
            "total": prices[drug_id] * quantity,
        })
    return pd.DataFrame(rows)


def add_initial_stock(rng, drugs, sales):
    """Stock inicial = unidades vendidas + margen aleatorio. Nunca queda por debajo de lo vendido."""
    sold = sales.groupby("drug_id")["quantity"].sum()
    drugs = drugs.copy()
    drugs["initial_stock"] = [
        int(sold.get(drug_id, 0)) + rng.randint(STOCK_MIN, STOCK_MAX)
        for drug_id in drugs["drug_id"]
    ]
    return drugs


def dirty_data(rng, customers, sales):
    """Agrega nulos y filas duplicadas a propósito, para que la limpieza tenga trabajo."""
    customers = customers.copy()
    sales = sales.copy()
    for df, columns in ((customers, ["full_name", "city"]), (sales, ["quantity"])):
        for column in columns:
            df[column] = df[column].astype(object)
            rows = rng.sample(range(len(df)), round(len(df) * NULL_RATE))
            df.loc[rows, column] = None
    n_duplicates = round(len(sales) * DUPLICATE_RATE)
    copies = sales.sample(n=n_duplicates, random_state=SEED)
    sales = pd.concat([sales, copies], ignore_index=True)
    return customers, sales

def write_sheet(writer, key, df):
    """Escribe una hoja con encabezados en español, encabezado en negrita y columnas ajustadas al contenido."""
    sheet_name = SHEET_NAMES[key]
    df.rename(columns=COLUMN_NAMES[key]).to_excel(writer, sheet_name=sheet_name, index=False)
    worksheet = writer.sheets[sheet_name]
    for column_cells in worksheet.columns:
        width = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
        worksheet.column_dimensions[column_cells[0].column_letter].width = width + 3
    for row in worksheet.iter_rows(min_row=2):
        for cell in row:
            if isinstance(cell.value, date):
                cell.number_format = "yyyy-mm-dd"
    for cell in worksheet[1]:
        cell.font = Font(bold=True)

def main():
    rng = random.Random(SEED)
    drugs = make_drugs(rng)
    customers = make_customers(rng)
    sales = make_sales(rng, drugs)
    drugs = add_initial_stock(rng, drugs, sales)

    customers, sales = dirty_data(rng, customers, sales)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl", date_format="yyyy-mm-dd") as writer:
        write_sheet(writer, "drugs", drugs)
        write_sheet(writer, "customers", customers)
        write_sheet(writer, "sales", sales)
    print(f"Archivo generado: {OUTPUT_PATH} (filas de sales incluyendo duplicados: {len(sales)})")


if __name__ == "__main__":
    main()