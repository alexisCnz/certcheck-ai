import json
import pandas as pd
from src.config import DATA_DIR, CERTIFICATES_DIR, ORDERS_DIR

def test_synthetic_dataset_exists():
    """Verifica que existan exactamente 20 PDFs, el CSV de POs y el JSON de Ground Truth."""
    # Verificar existencia de archivos clave
    csv_file = ORDERS_DIR / "purchase_orders.csv"
    gt_file = DATA_DIR / "ground_truth.json"
    
    assert csv_file.exists(), "No se encontró el CSV de órdenes de compra."
    assert gt_file.exists(), "No se encontró el archivo ground_truth.json."

    # Verificar que haya exactamente 20 PDFs en el directorio
    pdf_files = list(CERTIFICATES_DIR.glob("*.pdf"))
    assert len(pdf_files) == 20, f"Se esperaban 20 PDFs, pero se encontraron {len(pdf_files)}."

    # Verificar contenido de Ground Truth
    with open(gt_file, "r", encoding="utf-8") as f:
        gt_data = json.load(f)
    
    assert len(gt_data) == 20
    ok_cases = [c for c in gt_data if c["is_ok"]]
    err_cases = [c for c in gt_data if not c["is_ok"]]
    
    # 12 casos conformes y 8 con errores intencionales
    assert len(ok_cases) == 12, f"Se esperaban 12 casos conformes, se hallaron {len(ok_cases)}"
    assert len(err_cases) == 8, f"Se esperaban 8 casos con error, se hallaron {len(err_cases)}"

def test_purchase_orders_csv():
    """Verifica la integridad de las columnas del CSV de órdenes de compra."""
    csv_file = ORDERS_DIR / "purchase_orders.csv"
    df = pd.read_csv(csv_file)
    
    assert len(df) == 20
    required_cols = {"po_number", "expected_pn", "expected_qty", "expected_condition", "expected_sn"}
    assert required_cols.issubset(df.columns)
