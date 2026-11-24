"""Limpia el Excel de Farmaticas y deja un log con las métricas de la limpieza."""

import pandas as pd

import generate_excel as gen

INPUT_PATH = gen.OUTPUT_PATH
OUTPUT_PATH = INPUT_PATH.parent / "farmaticas_datos_limpios.xlsx"
LOG_PATH = INPUT_PATH.parent / "limpieza_log.txt"
MISSING_TEXT = "Sin dato"


def read_raw(path):
    """Lee el Excel (hojas y encabezados en español) y devuelve DataFrames con nombres internos en inglés."""
    raw = pd.read_excel(path, sheet_name=None)
    frames = {}
    for key, sheet_name in gen.SHEET_NAMES.items():
        reverse = {spanish: english for english, spanish in gen.COLUMN_NAMES[key].items()}
        frames[key] = raw[sheet_name].rename(columns=reverse)
    return frames["drugs"], frames["customers"], frames["sales"]


def stock_by_drug(drugs, sales):
    """Inventario = existencias iniciales - unidades vendidas."""
    sold = sales.groupby("drug_id")["quantity"].sum().reindex(drugs["drug_id"]).fillna(0)
    return drugs.set_index("drug_id")["initial_stock"] - sold


def clean_customers(customers, log):
    customers = customers.copy()
    for column in ("full_name", "city"):
        n_missing = int(customers[column].isna().sum())
        customers[column] = customers[column].fillna(MISSING_TEXT)
        label = gen.COLUMN_NAMES["customers"][column]
        log.append(f"Clientes: {n_missing} valores nulos en '{label}' reemplazados por '{MISSING_TEXT}'")
    return customers


def clean_sales(sales, drugs, log):
    before = len(sales)
    sales = sales.drop_duplicates().reset_index(drop=True)
    log.append(f"Ventas: {before - len(sales)} filas duplicadas eliminadas (de {before} a {len(sales)})")

    # La cantidad nula se recupera con total / precio unitario
    missing = sales["quantity"].isna()
    n_missing = int(missing.sum())
    prices = drugs.set_index("drug_id")["unit_price"]
    sales.loc[missing, "quantity"] = (
        sales.loc[missing, "total"] / sales.loc[missing, "drug_id"].map(prices)
    ).round()
    unrecovered = sales["quantity"].isna()
    n_unrecovered = int(unrecovered.sum())
    log.append(f"Ventas: {n_missing - n_unrecovered} de {n_missing} cantidades nulas recuperadas (total / precio unitario)")
    if n_unrecovered:
        sales = sales[~unrecovered].reset_index(drop=True)
        log.append(f"Ventas: {n_unrecovered} filas sin cantidad recuperable eliminadas")
    sales["quantity"] = sales["quantity"].astype(int)
    return sales


def null_summary(key, df):
    nulls = {gen.COLUMN_NAMES[key][c]: int(n) for c, n in df.isna().sum().items() if n}
    return nulls if nulls else "ninguno"


def main():
    drugs, customers, sales_raw = read_raw(INPUT_PATH)

    log = ["LOG DE LIMPIEZA - FARMATICAS", "", "Datos de entrada:"]
    for key, df in (("drugs", drugs), ("customers", customers), ("sales", sales_raw)):
        log.append(f"- {gen.SHEET_NAMES[key]}: {len(df)} filas, nulos: {null_summary(key, df)}")
    log += ["", "Acciones:"]

    customers_clean = clean_customers(customers, log)
    sales_clean = clean_sales(sales_raw, drugs, log)

    stock_before = stock_by_drug(drugs, sales_raw)
    stock_after = stock_by_drug(drugs, sales_clean)
    log += [
        "",
        "Efecto sobre el inventario:",
        f"- Unidades vendidas: antes {int(sales_raw['quantity'].sum())}, después {int(sales_clean['quantity'].sum())}",
        f"- Medicamentos con inventario negativo: antes {int((stock_before < 0).sum())}, después {int((stock_after < 0).sum())}",
    ]

    with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
        gen.write_sheet(writer, "drugs", drugs)
        gen.write_sheet(writer, "customers", customers_clean)
        gen.write_sheet(writer, "sales", sales_clean)
    LOG_PATH.write_text("\n".join(log) + "\n", encoding="utf-8")
    print("\n".join(log))
    print(f"\nArchivo limpio: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()