"""
Pruebas exhaustivas para el motor de reglas determinísticas de CertCheck AI.
Cubre pruebas unitarias de cada regla y prueba de integración de extremo a extremo con los 20 casos sintéticos.
"""

import json
from datetime import datetime
import pytest

from src.config import DATA_DIR, CERTIFICATES_DIR
from src.extractor.schemas import CertificateData
from src.extractor.mock_extractor import MockCertificateExtractor
from src.validator.models import (
    ValidationStatus,
    AlertSeverity,
    PurchaseOrderInput
)
from src.validator.rules import (
    check_part_number,
    check_serial_number,
    check_quantity,
    check_condition,
    check_traceability_and_signatures,
    check_shelf_life
)
from src.validator.engine import ConformityValidatorEngine


def test_rule_part_number_exact_and_formatting():
    """Valida coincidencia exacta y diferencias admisibles de formato (guiones)."""
    # 1. Coincidencia exacta -> 0 alertas
    alerts = check_part_number("139-00-854-22NK", "139-00-854-22NK")
    assert len(alerts) == 0

    # 2. Diferencia en guiones -> Alerta INFO (no bloqueante)
    alerts = check_part_number("139-00-854-22NK", "1390085422NK")
    assert len(alerts) == 1
    assert alerts[0].severity == AlertSeverity.INFO


def test_rule_part_number_divergence():
    """Valida detección de discrepancia de sufijo y dígitos transpuestos."""
    # Sufijo cambiado (NK vs NL) -> Distancia Levenshtein 1 -> ERR_PN_DIVERGENCE
    alerts = check_part_number("139-00-854-22NK", "139-00-854-22NL")
    assert len(alerts) == 1
    assert alerts[0].code == "ERR_PN_DIVERGENCE"
    assert alerts[0].severity == AlertSeverity.CRITICAL

    # Dígitos transpuestos (0158 vs 0185) -> Distancia Levenshtein 2 -> ERR_PN_DIVERGENCE
    alerts = check_part_number("740-0158-001", "740-0185-001")
    assert len(alerts) == 1
    assert alerts[0].code == "ERR_PN_DIVERGENCE"


def test_rule_serial_typo_levenshtein():
    """Valida detección de errores de tipeo en seriales con similitud Levenshtein y O vs 0."""
    # Letra O en vez de número 0 -> WARN_SERIAL_TYPO_SUSPECT (Amarillo)
    alerts = check_serial_number("SN-84902-B", "SN-849O2-B")
    assert len(alerts) == 1
    assert alerts[0].code == "WARN_SERIAL_TYPO_SUSPECT"
    assert alerts[0].severity == AlertSeverity.WARNING

    # Serial totalmente distinto -> ERR_SERIAL_MISMATCH (Rojo)
    alerts = check_serial_number("SN-84902-B", "SN-99999-Z")
    assert len(alerts) == 1
    assert alerts[0].code == "ERR_SERIAL_MISMATCH"
    assert alerts[0].severity == AlertSeverity.CRITICAL


def test_rule_quantity_shortage_and_excess():
    """Valida detección de entregas parciales y excesos."""
    # Entrega parcial: PO pide 100, certificado dice 80
    alerts = check_quantity(expected_qty=100, cert_qty=80)
    assert len(alerts) == 1
    assert alerts[0].code == "WARN_QTY_SHORTAGE"
    assert alerts[0].severity == AlertSeverity.WARNING

    # Exceso de entrega: PO pide 10, certificado dice 15
    alerts = check_quantity(expected_qty=10, cert_qty=15)
    assert len(alerts) == 1
    assert alerts[0].code == "WARN_QTY_EXCESS"


def test_rule_condition_mismatch():
    """Valida discrepancia de condición (ej: NEW vs OVERHAULED)."""
    # Se pide NEW pero llega OVERHAULED -> Alerta Crítica
    alerts = check_condition(expected_cond="NEW", cert_status="OVERHAULED")
    assert len(alerts) == 1
    assert alerts[0].code == "ERR_CONDITION_MISMATCH"
    assert alerts[0].severity == AlertSeverity.CRITICAL

    # Equivalencia de alias: FACTORY NEW vs NEW -> Coincide
    alerts = check_condition(expected_cond="FACTORY NEW", cert_status="NEW")
    assert len(alerts) == 0


def test_rule_missing_signatures():
    """Valida certificado no válido por falta de firma o fecha."""
    cert = CertificateData(
        part_number="3110-0012",
        is_signed=False,           # Sin firma
        signature_date=None,       # Sin fecha
        form_tracking_number=""    # Sin tracking
    )
    alerts = check_traceability_and_signatures(cert)
    codes = [a.code for a in alerts]
    assert "ERR_MISSING_SIGNATURE" in codes
    assert "ERR_MISSING_SIGN_DATE" in codes


def test_rule_shelf_life_expired():
    """Valida detección de shelf life vencido respecto a fecha de referencia."""
    cert = CertificateData(
        part_number="PR-1422-B2",
        shelf_life_expiry="30-JUN-2022",
        remarks="CURE DATE: 2Q2020. EXPIRY DATE: 30-JUN-2022."
    )
    # Evaluado en 2026 -> Material vencido
    ref_date = datetime(2026, 4, 1)
    alerts = check_shelf_life(cert, reference_date=ref_date)
    assert len(alerts) == 1
    assert alerts[0].code == "ERR_SHELF_LIFE_EXPIRED"
    assert alerts[0].severity == AlertSeverity.CRITICAL


def test_full_dataset_validation_engine():
    """
    Prueba de integración masiva:
    Evalúa los 20 casos sintéticos del Ground Truth a través del motor de validación.
    Garantiza:
    - 100% de los 12 casos OK resultan en PASS (Verde).
    - 100% de los 8 casos con error resultan en FAIL o REVIEW (Rojo o Amarillo).
    """
    gt_path = DATA_DIR / "ground_truth.json"
    with open(gt_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    extractor = MockCertificateExtractor(gt_path)
    engine = ConformityValidatorEngine(reference_date=datetime(2026, 4, 1))

    results = []
    for case in cases:
        pdf_path = CERTIFICATES_DIR / case["file_name"]
        cert = extractor.extract(pdf_path)
        po = PurchaseOrderInput(
            po_number=case["po_number"],
            expected_pn=case["expected_pn"],
            expected_qty=case["expected_qty"],
            expected_condition=case["expected_condition"],
            expected_sn=case["expected_sn"]
        )

        report = engine.validate(cert, po)
        results.append({
            "case_id": case["case_id"],
            "is_ok_ground_truth": case["is_ok"],
            "expected_error": case["error_type"],
            "status": report.status,
            "alerts_count": len(report.alerts)
        })

        if case["is_ok"]:
            assert report.status == ValidationStatus.PASS, (
                f"Falso Positivo en {case['case_id']}: esperado PASS pero obtuvo {report.status}. "
                f"Alertas: {[a.message for a in report.alerts]}"
            )
        else:
            assert report.status in [ValidationStatus.FAIL, ValidationStatus.REVIEW], (
                f"Falso Negativo en {case['case_id']}: esperado FAIL/REVIEW pero obtuvo PASS."
            )

    print(f"\nEvaluados {len(results)} casos con 100% de concordancia con el Ground Truth.")
