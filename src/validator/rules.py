"""
Reglas de validación determinísticas para cuarentena y control de calidad aeronáutico.
Cero alucinaciones: implementadas en Python puro con algoritmos determinísticos.
"""

import re
from typing import List, Optional
from datetime import datetime
import Levenshtein

from src.extractor.schemas import CertificateData
from src.validator.models import (
    ValidationAlert,
    AlertSeverity,
    PurchaseOrderInput
)


def normalize_string(text: Optional[str]) -> str:
    """Elimina espacios extra y convierte a mayúsculas."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text.strip()).upper()


def strip_pn_separators(pn: str) -> str:
    """Elimina guiones, barras y espacios para comparación estructural profunda."""
    return re.sub(r"[-_/\s]", "", pn).upper()


def check_part_number(expected_pn: str, cert_pn: str) -> List[ValidationAlert]:
    """
    Valida el Part Number contrastando la PO contra el certificado.
    Detecta coincidencias exactas, variaciones de formato y discrepancias tipográficas.
    """
    alerts = []
    norm_expected = normalize_string(expected_pn)
    norm_cert = normalize_string(cert_pn)

    # 1. Coincidencia exacta
    if norm_expected == norm_cert:
        return alerts

    # 2. Coincidencia estructural sin guiones/separadores
    if strip_pn_separators(norm_expected) == strip_pn_separators(norm_cert):
        alerts.append(
            ValidationAlert(
                code="INFO_PN_FORMAT_DIFFERENCE",
                severity=AlertSeverity.INFO,
                field="part_number",
                message=f"El Part Number coincide estructuralmente pero difiere en guiones/espacios: PO '{norm_expected}' vs Cert '{norm_cert}'.",
                details={"expected": norm_expected, "certified": norm_cert}
            )
        )
        return alerts

    # 3. Discrepancia real: calcular similitud con Levenshtein
    dist = Levenshtein.distance(norm_expected, norm_cert)
    ratio = Levenshtein.ratio(norm_expected, norm_cert)

    if dist <= 2 or ratio >= 0.80:
        alerts.append(
            ValidationAlert(
                code="ERR_PN_DIVERGENCE",
                severity=AlertSeverity.CRITICAL,
                field="part_number",
                message=(
                    f"DIVERGENCIA DE PART NUMBER: Se esperaba '{norm_expected}', pero el certificado indica '{norm_cert}'. "
                    f"Diferencia mínima detectada (Distancia Levenshtein: {dist}, Similitud: {ratio:.0%}). "
                    "Posible sufijo cambiado o dígito transpuesto."
                ),
                details={"expected": norm_expected, "certified": norm_cert, "distance": dist, "ratio": ratio}
            )
        )
    else:
        alerts.append(
            ValidationAlert(
                code="ERR_PN_MISMATCH",
                severity=AlertSeverity.CRITICAL,
                field="part_number",
                message=f"PART NUMBER NO COINCIDE: Se esperaba '{norm_expected}', pero el certificado indica '{norm_cert}'.",
                details={"expected": norm_expected, "certified": norm_cert, "distance": dist, "ratio": ratio}
            )
        )

    return alerts


def check_serial_number(expected_sn: Optional[str], cert_sn: Optional[str]) -> List[ValidationAlert]:
    """
    Valida el número de serie.
    Utiliza similitud Levenshtein y heurística de sustitución visual común (ej: 'O' vs '0', 'I' vs '1').
    """
    alerts = []
    if not expected_sn or normalize_string(expected_sn) in ["N/A", "NA", "NONE", ""]:
        # La PO no especificaba un serial obligatorio
        return alerts

    norm_expected = normalize_string(expected_sn)
    norm_cert = normalize_string(cert_sn)

    if norm_cert in ["N/A", "NA", "NONE", ""]:
        alerts.append(
            ValidationAlert(
                code="ERR_SERIAL_MISSING",
                severity=AlertSeverity.CRITICAL,
                field="serial_number",
                message=f"La PO requiere el serial '{norm_expected}', pero el certificado indica 'N/A' o está vacío.",
                details={"expected": norm_expected, "certified": norm_cert}
            )
        )
        return alerts

    if norm_expected == norm_cert:
        return alerts

    dist = Levenshtein.distance(norm_expected, norm_cert)

    # Detectar sustitución visual típica (O por 0, I por 1, etc.)
    visual_expected = norm_expected.replace("O", "0").replace("I", "1").replace("B", "8")
    visual_cert = norm_cert.replace("O", "0").replace("I", "1").replace("B", "8")
    is_visual_typo = (visual_expected == visual_cert)

    if dist <= 2 or is_visual_typo:
        alerts.append(
            ValidationAlert(
                code="WARN_SERIAL_TYPO_SUSPECT",
                severity=AlertSeverity.WARNING,
                field="serial_number",
                message=(
                    f"SERIAL SOSPECHOSO DE ERROR TIPOGRÁFICO: PO espera '{norm_expected}', 8130 indica '{norm_cert}'. "
                    f"(Distancia Levenshtein: {dist}{' - Error visual O/0 o I/1' if is_visual_typo else ''}). "
                    "Se recomienda inspeccionar visualmente la placa de datos físicos del componente."
                ),
                details={"expected": norm_expected, "certified": norm_cert, "distance": dist, "is_visual_typo": is_visual_typo}
            )
        )
    else:
        alerts.append(
            ValidationAlert(
                code="ERR_SERIAL_MISMATCH",
                severity=AlertSeverity.CRITICAL,
                field="serial_number",
                message=f"SERIAL NO COINCIDE: PO especifica '{norm_expected}', pero el certificado ampara '{norm_cert}'.",
                details={"expected": norm_expected, "certified": norm_cert, "distance": dist}
            )
        )

    return alerts


def check_quantity(expected_qty: Optional[int], cert_qty: Optional[int]) -> List[ValidationAlert]:
    """Valida que la cantidad física amparada concuerde con lo ordenado."""
    alerts = []
    if expected_qty is None:
        return alerts

    if cert_qty is None or cert_qty <= 0:
        alerts.append(
            ValidationAlert(
                code="WARN_QTY_UNDEFINED",
                severity=AlertSeverity.WARNING,
                field="quantity",
                message=f"Cantidad no especificada en el certificado. Se esperaban {expected_qty} unidades.",
                details={"expected": expected_qty, "certified": cert_qty}
            )
        )
        return alerts

    if cert_qty < expected_qty:
        alerts.append(
            ValidationAlert(
                code="WARN_QTY_SHORTAGE",
                severity=AlertSeverity.WARNING,
                field="quantity",
                message=f"ENTREGA PARCIAL O CANTIDAD MENOR: PO solicita {expected_qty} unidades, pero el certificado solo ampara {cert_qty}.",
                details={"expected": expected_qty, "certified": cert_qty}
            )
        )
    elif cert_qty > expected_qty:
        alerts.append(
            ValidationAlert(
                code="WARN_QTY_EXCESS",
                severity=AlertSeverity.WARNING,
                field="quantity",
                message=f"EXCESO DE CANTIDAD: El certificado ampara {cert_qty} unidades, superando las {expected_qty} ordenadas en la PO.",
                details={"expected": expected_qty, "certified": cert_qty}
            )
        )

    return alerts


def check_condition(expected_cond: Optional[str], cert_status: Optional[str]) -> List[ValidationAlert]:
    """Valida la condición o estado del material (ej: NEW vs OVERHAULED)."""
    alerts = []
    if not expected_cond:
        return alerts

    # Mapeo de equivalencias estándar en la industria aeronáutica
    condition_aliases = {
        "NEW": ["NEW", "NE", "FN", "FACTORY NEW", "NUEVO"],
        "OVERHAULED": ["OVERHAULED", "OH", "REACONDICIONADO"],
        "REPAIRED": ["REPAIRED", "RP", "REPARADO"],
        "INSPECTED/TESTED": ["INSPECTED/TESTED", "INSPECTED", "TESTED", "SV", "SERVICEABLE", "IN"],
        "MODIFIED": ["MODIFIED", "MOD", "MODIFICADO"]
    }

    norm_expected = normalize_string(expected_cond)
    norm_cert = normalize_string(cert_status)

    # Buscar familia de la condición esperada
    expected_family = None
    for family, aliases in condition_aliases.items():
        if norm_expected in aliases or any(alias in norm_expected for alias in aliases):
            expected_family = family
            break

    # Buscar familia de la condición certificada
    cert_family = None
    for family, aliases in condition_aliases.items():
        if norm_cert in aliases or any(alias in norm_cert for alias in aliases):
            cert_family = family
            break

    match = False
    if expected_family and cert_family:
        match = (expected_family == cert_family)
    else:
        match = (norm_expected == norm_cert)

    if not match:
        alerts.append(
            ValidationAlert(
                code="ERR_CONDITION_MISMATCH",
                severity=AlertSeverity.CRITICAL,
                field="status_work",
                message=f"CONDICIÓN DISCREPANTE: La PO requería condición '{norm_expected}', pero el certificado indica '{norm_cert}'.",
                details={"expected": norm_expected, "certified": norm_cert}
            )
        )

    return alerts


def check_traceability_and_signatures(cert: CertificateData) -> List[ValidationAlert]:
    """
    Verifica los requisitos legales del certificado:
    - Firma en Bloque 13b o 14b
    - Fecha de emisión
    - Form Tracking Number
    """
    alerts = []

    if not cert.is_signed:
        alerts.append(
            ValidationAlert(
                code="ERR_MISSING_SIGNATURE",
                severity=AlertSeverity.CRITICAL,
                field="signatures",
                message="TRAZABILIDAD ROTA / CERTIFICADO INVÁLIDO: No contiene firma de autorización en Bloques 13/14.",
                details={"is_signed": cert.is_signed}
            )
        )

    if not cert.signature_date or not cert.signature_date.strip():
        alerts.append(
            ValidationAlert(
                code="ERR_MISSING_SIGN_DATE",
                severity=AlertSeverity.CRITICAL,
                field="signature_date",
                message="Falta fecha de firma y liberación en Bloque 13e/14e del certificado.",
                details={"signature_date": cert.signature_date}
            )
        )

    if not cert.form_tracking_number or not cert.form_tracking_number.strip():
        alerts.append(
            ValidationAlert(
                code="WARN_MISSING_TRACKING",
                severity=AlertSeverity.WARNING,
                field="form_tracking_number",
                message="Bloque 3 vacío: No se especificó el Form Tracking Number.",
                details={"form_tracking_number": cert.form_tracking_number}
            )
        )

    return alerts


def parse_aero_date(date_str: str) -> Optional[datetime]:
    """Intenta parsear formatos comunes de fecha aeronáutica (ej: 31-MAR-2022, 14-03-2026, 2026-03-14)."""
    clean_date = date_str.strip().upper()
    formats = [
        "%d-%b-%Y",  # 31-MAR-2022
        "%d/%b/%Y",  # 31/MAR/2022
        "%d.%b.%Y",  # 31.MAR.2022
        "%Y-%m-%d",  # 2022-03-31
        "%d-%m-%Y",  # 31-03-2022
        "%d/%m/%Y",  # 31/03/2022
    ]
    for fmt in formats:
        try:
            return datetime.strptime(clean_date, fmt)
        except ValueError:
            continue
    return None


def check_shelf_life(cert: CertificateData, reference_date: Optional[datetime] = None) -> List[ValidationAlert]:
    """
    Verifica si el material posee caducidad (Shelf Life) y si está vencido o próximo a vencer.
    Analiza tanto los campos explícitos de shelf_life como las notas del Bloque 12.
    """
    alerts = []
    # Fecha de referencia para evaluación (por defecto hoy, o 2026 para testing consistente)
    eval_date = reference_date or datetime.now()

    # Buscar fecha de expiración en campos estructurados o regex en remarks
    expiry_str = cert.shelf_life_expiry
    if not expiry_str and cert.remarks:
        match = re.search(r"EXPIR(?:Y|ATION)(?:\s+DATE)?[:\s]+([0-9]{1,2}[-/.][A-Za-z0-9]{3}[-/.][0-9]{4})", cert.remarks, re.IGNORECASE)
        if match:
            expiry_str = match.group(1)

    if not expiry_str:
        return alerts

    parsed_expiry = parse_aero_date(expiry_str)
    if not parsed_expiry:
        alerts.append(
            ValidationAlert(
                code="WARN_SHELF_LIFE_UNPARSED",
                severity=AlertSeverity.WARNING,
                field="shelf_life",
                message=f"Se detectó información de Shelf Life ('{expiry_str}') pero el formato de fecha requiere revisión manual.",
                details={"raw_expiry": expiry_str}
            )
        )
        return alerts

    # Comparación de fechas
    days_remaining = (parsed_expiry - eval_date).days

    if days_remaining < 0:
        alerts.append(
            ValidationAlert(
                code="ERR_SHELF_LIFE_EXPIRED",
                severity=AlertSeverity.CRITICAL,
                field="shelf_life",
                message=(
                    f"MATERIAL CADUCADO (SHELF LIFE VENCIDO): El producto expiró el {parsed_expiry.strftime('%d-%b-%Y')} "
                    f"({abs(days_remaining)} días vencido). Material no apto para instalación aeronáutica."
                ),
                details={"expiry_date": parsed_expiry.strftime("%Y-%m-%d"), "days_expired": abs(days_remaining)}
            )
        )
    elif days_remaining <= 90:
        alerts.append(
            ValidationAlert(
                code="WARN_SHELF_LIFE_EXPIRING",
                severity=AlertSeverity.WARNING,
                field="shelf_life",
                message=(
                    f"MATERIAL PRÓXIMO A VENCER: Expirará el {parsed_expiry.strftime('%d-%b-%Y')} "
                    f"(restan {days_remaining} días de vida útil)."
                ),
                details={"expiry_date": parsed_expiry.strftime("%Y-%m-%d"), "days_remaining": days_remaining}
            )
        )

    return alerts
