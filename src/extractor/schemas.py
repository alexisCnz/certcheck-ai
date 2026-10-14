"""
Esquemas de datos con Pydantic v2 para el certificado de aeronavegabilidad.
Define la estructura exacta que el LLM debe extraer del documento.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CertificateData(BaseModel):
    """
    Modelo estructurado de datos extraídos de un certificado FAA Form 8130-3 o EASA Form 1.
    Mapea directamente los bloques del formulario estándar aeronáutico.
    """
    form_tracking_number: Optional[str] = Field(
        default=None,
        description="Bloque 3: Número de seguimiento único del formulario (Tracking Number)."
    )
    organization_name: Optional[str] = Field(
        default=None,
        description="Bloque 4: Nombre de la organización o taller emisor."
    )
    organization_address: Optional[str] = Field(
        default=None,
        description="Bloque 4: Dirección y país de la organización emisora."
    )
    work_order_po: Optional[str] = Field(
        default=None,
        description="Bloque 5: Nexo con la orden de compra, Work Order, contrato o factura."
    )
    item: Optional[str] = Field(
        default="1",
        description="Bloque 6: Número de ítem o renglón en el certificado."
    )
    description: str = Field(
        default="",
        description="Bloque 7: Descripción o nomenclatura de la parte aeronáutica."
    )
    part_number: str = Field(
        ...,
        description="Bloque 8: Número de parte (Part Number / PN) principal."
    )
    quantity: Optional[int] = Field(
        default=1,
        description="Bloque 9: Cantidad amparada por el certificado."
    )
    serial_number: Optional[str] = Field(
        default="N/A",
        description="Bloque 10: Número de serie o lote (Serial / Batch Number). Si no aplica, 'N/A'."
    )
    status_work: str = Field(
        default="UNKNOWN",
        description="Bloque 11: Estado o condición del material (ej: NEW, OVERHAULED, REPAIRED, INSPECTED/TESTED, MODIFIED)."
    )
    remarks: Optional[str] = Field(
        default="",
        description="Bloque 12: Observaciones, autorizaciones TSO/PMA, y datos de trazabilidad."
    )
    cure_date: Optional[str] = Field(
        default=None,
        description="Fecha de cura (Cure Date) identificada en observaciones, si aplica (ej: 1Q2025)."
    )
    shelf_life_expiry: Optional[str] = Field(
        default=None,
        description="Fecha de vencimiento de vida útil (Shelf Life Expiry) en observaciones, si aplica (ej: 31-MAR-2022)."
    )
    is_signed: bool = Field(
        default=False,
        description="Indica si el certificado cuenta con firma en Bloque 13b (fabricación) o 14b (mantenimiento)."
    )
    authorized_name: Optional[str] = Field(
        default=None,
        description="Bloque 13d o 14d: Nombre de la persona autorizada que firma."
    )
    approval_number: Optional[str] = Field(
        default=None,
        description="Bloque 13c o 14c: Número de certificado o autorización del inspector/taller (DMIR, CRS, etc.)."
    )
    signature_date: Optional[str] = Field(
        default=None,
        description="Bloque 13e o 14e: Fecha de firma y liberación del certificado."
    )
    form_type: str = Field(
        default="FAA Form 8130-3",
        description="Tipo de certificado identificado (FAA 8130-3 o EASA Form 1)."
    )

    @field_validator("part_number", mode="before")
    @classmethod
    def clean_part_number(cls, v: str) -> str:
        """Limpia espacios en blanco alrededor del PN."""
        if isinstance(v, str):
            return v.strip().upper()
        return str(v)

    @field_validator("status_work", mode="before")
    @classmethod
    def normalize_status(cls, v: str) -> str:
        """Normaliza el estado/condición a mayúsculas para comparaciones determinísticas."""
        if isinstance(v, str):
            return v.strip().upper()
        return "UNKNOWN"

    @field_validator("serial_number", mode="before")
    @classmethod
    def clean_serial(cls, v: str) -> str:
        """Estandariza seriales vacíos o no aplicables."""
        if not v or str(v).strip().upper() in ["N/A", "NA", "NONE", "NO", "-"]:
            return "N/A"
        return str(v).strip().upper()
