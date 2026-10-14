"""
Extractor simulado (Mock) para pruebas unitarias sin conexión a internet ni consumo de API tokens.
Utiliza heuristics simples y el archivo ground_truth.json si está disponible.
"""

import json
from pathlib import Path
from typing import Optional
import pdfplumber

from src.config import DATA_DIR
from src.extractor.base import BaseCertificateExtractor
from src.extractor.schemas import CertificateData


class MockCertificateExtractor(BaseCertificateExtractor):
    """Extractor mock determinístico para testing e integración continua."""

    def __init__(self, ground_truth_file: Optional[Path] = None):
        self.gt_file = ground_truth_file or (DATA_DIR / "ground_truth.json")
        self._lookup = {}
        if self.gt_file.exists():
            with open(self.gt_file, "r", encoding="utf-8") as f:
                cases = json.load(f)
                for c in cases:
                    self._lookup[c["file_name"]] = c

    def extract(self, pdf_path: Path) -> CertificateData:
        """Devuelve un objeto CertificateData basado en el archivo PDF."""
        file_name = pdf_path.name

        # Si el archivo está en nuestro dataset sintético, usamos el Ground Truth
        if file_name in self._lookup:
            data = self._lookup[file_name]
            return CertificateData(
                form_tracking_number=data["tracking_no"],
                organization_name=data["org_name"],
                organization_address=data["org_address"],
                work_order_po=data["work_order_po"],
                item=data["item"],
                description=data["description"],
                part_number=data["cert_pn"],
                quantity=data["cert_qty"],
                serial_number=data["cert_sn"],
                status_work=data["cert_status"],
                remarks=data["remarks"],
                cure_date="1Q2025" if "1Q2025" in data["remarks"] else ("2Q2020" if "2Q2020" in data["remarks"] else None),
                shelf_life_expiry="31-MAR-2030" if "31-MAR-2030" in data["remarks"] else ("30-JUN-2022" if "30-JUN-2022" in data["remarks"] else None),
                is_signed=bool(data["auth_name"]),
                authorized_name=data["auth_name"] if data["auth_name"] else None,
                approval_number=data["auth_no"] if data["auth_no"] else None,
                signature_date=data["auth_date"] if data["auth_date"] else None,
                form_type="FAA Form 8130-3"
            )

        # Fallback genérico para cualquier otro PDF
        return CertificateData(
            form_tracking_number="MOCK-TRACK-001",
            organization_name="Mock Aviation Corp",
            organization_address="100 Mock St, Mock City",
            work_order_po="PO-MOCK-001",
            item="1",
            description="MOCK AERONAUTICAL COMPONENT",
            part_number="MOCK-PN-01",
            quantity=1,
            serial_number="MOCK-SN-99",
            status_work="NEW",
            remarks="Mock test certificate",
            is_signed=True,
            authorized_name="Mock Inspector",
            approval_number="DMIR-000000",
            signature_date="01-JAN-2026",
            form_type="FAA Form 8130-3"
        )
