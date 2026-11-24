import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import generate_excel as gen  # noqa: E402


def generate_to(monkeypatch, path):
    monkeypatch.setattr(gen, "OUTPUT_PATH", path)
    gen.main()
    raw = pd.read_excel(path, sheet_name=None)
    # Si falta una hoja en español, esto falla con KeyError
    return {key: raw[name] for key, name in gen.SHEET_NAMES.items()}


def test_sheets_and_row_counts(tmp_path, monkeypatch):
    sheets = generate_to(monkeypatch, tmp_path / "a.xlsx")
    assert list(sheets) == ["drugs", "customers", "sales"]
    assert len(sheets["drugs"]) == gen.N_DRUGS
    assert len(sheets["customers"]) == gen.N_CUSTOMERS
    assert len(sheets["sales"]) == gen.N_SALES + round(gen.N_SALES * gen.DUPLICATE_RATE)


def test_has_nulls_and_duplicates(tmp_path, monkeypatch):
    sheets = generate_to(monkeypatch, tmp_path / "a.xlsx")
    assert sheets["customers"].isna().any().any()
    assert sheets["sales"].duplicated().any()


def test_same_seed_same_output(tmp_path, monkeypatch):
    first = generate_to(monkeypatch, tmp_path / "1.xlsx")
    second = generate_to(monkeypatch, tmp_path / "2.xlsx")
    for name in first:
        pd.testing.assert_frame_equal(first[name], second[name])


def test_initial_stock_covers_sales():
    rng = random.Random(gen.SEED)
    drugs = gen.make_drugs(rng)
    sales = gen.make_sales(rng, drugs)
    drugs = gen.add_initial_stock(rng, drugs, sales)
    sold = sales.groupby("drug_id")["quantity"].sum().reindex(drugs["drug_id"]).fillna(0)
    assert (drugs["initial_stock"].values >= sold.values).all()

def test_spanish_headers(tmp_path, monkeypatch):
    sheets = generate_to(monkeypatch, tmp_path / "a.xlsx")
    for key, df in sheets.items():
        assert list(df.columns) == list(gen.COLUMN_NAMES[key].values())