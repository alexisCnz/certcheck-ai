"""
Modelos de datos para el motor de validación aeronáutica.
Define los estados del semáforo, tipos de alertas y el reporte de conformidad.
"""

from enum import Enum
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field

from src.extractor.schemas import CertificateData


class ValidationStatus(str, Enum):
    """Estado resultante del semáforo de conformidad."""
    PASS = "PASS"         # 🟢 Conforme / Aprobado para recepción
    REVIEW = "REVIEW"     # 🟡 Requiere revisión técnica / advertencia
    FAIL = "FAIL"         # 🔴 Rechazado / Material retenido en cuarentena


class AlertSeverity(str, Enum):
    """Nivel de severidad de una discrepancia detectada."""
    INFO = "INFO"         # Nota informativa (ej: formato de guiones normalizado)
    WARNING = "WARNING"   # Advertencia (ej: serial sospechoso de tipeo, entrega parcial)
    CRITICAL = "CRITICAL" # Discrepancia crítica (ej: PN divergente, shelf life vencido, sin firma)


class ValidationAlert(BaseModel):
    """Alerta individual emitida por una regla de validación."""
    code: str = Field(..., description="Código único de la alerta (ej: ERR_PN_DIVERGENCE)")
    severity: AlertSeverity = Field(..., description="Nivel de severidad (INFO, WARNING, CRITICAL)")
    field: str = Field(..., description="Campo involucrado (ej: part_number, serial_number, shelf_life)")
    message: str = Field(..., description="Descripción clara y legible para el usuario de cuarentena")
    details: Optional[dict] = Field(default=None, description="Datos de soporte técnico o valores comparados")


class PurchaseOrderInput(BaseModel):
    """Datos de la Orden de Compra (PO) a contrastar contra el certificado."""
    po_number: str = Field(..., description="Número de la orden de compra (ej: PO-2026-1001)")
    expected_pn: str = Field(..., description="Part Number esperado según la orden de compra")
    expected_qty: Optional[int] = Field(default=None, description="Cantidad esperada (opcional)")
    expected_condition: Optional[str] = Field(default=None, description="Condición esperada (ej: NEW, OVERHAULED)")
    expected_sn: Optional[str] = Field(default=None, description="Serial Number esperado, si aplica")


class ValidationReport(BaseModel):
    """Reporte integral consolidado de validación y veredicto de semáforo."""
    status: ValidationStatus
    traffic_light: str = Field(..., description="Emoji y texto del semáforo (🟢 CONFORME, 🟡 REVISAR, 🔴 RECHAZAR)")
    summary: str
    alerts: List[ValidationAlert] = Field(default_factory=list)
    certificate_data: CertificateData
    purchase_order: PurchaseOrderInput
    evaluated_at: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    @property
    def is_acceptable(self) -> bool:
        """Retorna True solo si el estatus es PASS."""
        return self.status == ValidationStatus.PASS
