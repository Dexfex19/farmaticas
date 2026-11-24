import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import clean_data as clean  # noqa: E402
import generate_excel as gen  # noqa: E402


def run_pipeline(monkeypatch, tmp_path):
    raw_path = tmp_path / "raw.xlsx"
    monkeypatch.setattr(gen, "OUTPUT_PATH", raw_path)
    gen.main()
    monkeypatch.setattr(clean, "INPUT_PATH", raw_path)
    monkeypatch.setattr(clean, "OUTPUT_PATH", tmp_path / "clean.xlsx")
    monkeypatch.setattr(clean, "LOG_PATH", tmp_path / "log.txt")
    clean.main()
    frames = clean.read_raw(tmp_path / "clean.xlsx")
    return frames, (tmp_path / "log.txt").read_text(encoding="utf-8")


def test_sales_are_clean(tmp_path, monkeypatch):
    (drugs, _, sales), _ = run_pipeline(monkeypatch, tmp_path)
    assert len(sales) == gen.N_SALES
    assert not sales.duplicated().any()
    assert not sales["quantity"].isna().any()
    prices = drugs.set_index("drug_id")["unit_price"]
    assert (sales["quantity"] * sales["drug_id"].map(prices) == sales["total"]).all()


def test_customers_have_no_nulls(tmp_path, monkeypatch):
    (_, customers, _), _ = run_pipeline(monkeypatch, tmp_path)
    assert not customers.isna().any().any()
    assert (customers == clean.MISSING_TEXT).any().any()


def test_no_negative_stock_after_cleaning(tmp_path, monkeypatch):
    (drugs, _, sales), _ = run_pipeline(monkeypatch, tmp_path)
    assert (clean.stock_by_drug(drugs, sales) >= 0).all()


def test_log_has_metrics(tmp_path, monkeypatch):
    _, log = run_pipeline(monkeypatch, tmp_path)
    assert "filas duplicadas eliminadas" in log
    assert "cantidades nulas recuperadas" in log