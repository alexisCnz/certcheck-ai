"""
Motor principal de validación de conformidad aeronáutica (Conformity Validator Engine).
Ejecuta todas las reglas determinísticas y genera el reporte consolidado con semáforo.
"""

from typing import List, Optional
from datetime import datetime

from src.extractor.schemas import CertificateData
from src.validator.models import (
    ValidationStatus,
    AlertSeverity,
    ValidationAlert,
    PurchaseOrderInput,
    ValidationReport
)
from src.validator.rules import (
    check_part_number,
    check_serial_number,
    check_quantity,
    check_condition,
    check_traceability_and_signatures,
    check_shelf_life
)


class ConformityValidatorEngine:
    """
    Motor determinístico de reglas para cotejo de certificados de aeronavegabilidad
    contra especificaciones de órdenes de compra (PO).
    """

    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Args:
            reference_date: Fecha de referencia para evaluación de shelf-life (por defecto fecha actual).
        """
        self.reference_date = reference_date

    def validate(self, cert: CertificateData, po: PurchaseOrderInput) -> ValidationReport:
        """
        Ejecuta la suite completa de reglas de negocio sobre el certificado y la PO.
        
        Args:
            cert: Datos extraídos del certificado FAA 8130-3 / EASA Form 1.
            po: Datos de la orden de compra esperada.
            
        Returns:
            ValidationReport: Reporte con veredicto de semáforo, resumen y lista de alertas.
        """
        alerts: List[ValidationAlert] = []

        # 1. Regla crítica: Cotejo de Part Number
        alerts.extend(check_part_number(po.expected_pn, cert.part_number))

        # 2. Regla de Serial Number (Levenshtein y sustituciones)
        alerts.extend(check_serial_number(po.expected_sn, cert.serial_number))

        # 3. Regla de Cantidad
        alerts.extend(check_quantity(po.expected_qty, cert.quantity))

        # 4. Regla de Condición (NEW vs OVERHAULED, etc.)
        alerts.extend(check_condition(po.expected_condition, cert.status_work))

        # 5. Regla de Trazabilidad y Firmas de Autorización
        alerts.extend(check_traceability_and_signatures(cert))

        # 6. Regla de Shelf Life / Vida Útil
        alerts.extend(check_shelf_life(cert, reference_date=self.reference_date))

        # Determinar el semáforo final
        has_critical = any(a.severity == AlertSeverity.CRITICAL for a in alerts)
        has_warning = any(a.severity == AlertSeverity.WARNING for a in alerts)

        if has_critical:
            status = ValidationStatus.FAIL
            traffic_light = "🔴 RECHAZAR / CUARENTENA"
            summary = "Se detectaron discrepancias críticas. El material NO debe ser liberado de cuarentena sin disposición técnica."
        elif has_warning:
            status = ValidationStatus.REVIEW
            traffic_light = "🟡 REVISIÓN REQUERIDA"
            summary = "Se detectaron advertencias no críticas (posible error de tipeo o entrega parcial). Requiere verificación física del inspector."
        else:
            status = ValidationStatus.PASS
            traffic_light = "🟢 CONFORME / APROBADO"
            summary = "Conformidad total. Todos los parámetros coinciden y el certificado cuenta con trazabilidad válida."

        return ValidationReport(
            status=status,
            traffic_light=traffic_light,
            summary=summary,
            alerts=alerts,
            certificate_data=cert,
            purchase_order=po
        )
