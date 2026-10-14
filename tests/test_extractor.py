"""
Pruebas unitarias para los esquemas Pydantic y los extractores documentales.
"""

import pytest
from src.config import CERTIFICATES_DIR
from src.extractor.schemas import CertificateData
from src.extractor.mock_extractor import MockCertificateExtractor
from src.extractor.gemini_extractor import GeminiCertificateExtractor


def test_certificate_data_schema_valid():
    """Verifica que el modelo Pydantic valide y normalice correctamente los campos."""
    raw_data = {
        "form_tracking_number": "TRK-2026-99",
        "organization_name": "AeroTest Inc.",
        "description": "FLAP ACTUATOR",
        "part_number": "  139-00-854-22nk  ",  # con espacios y minúsculas
        "quantity": 2,
        "serial_number": "na",                 # debe normalizarse a N/A
        "status_work": "new",                  # debe normalizarse a NEW
        "is_signed": True,
        "authorized_name": "J. Doe",
        "signature_date": "10-MAR-2026"
    }
    
    cert = CertificateData(**raw_data)
    assert cert.part_number == "139-00-854-22NK"
    assert cert.serial_number == "N/A"
    assert cert.status_work == "NEW"
    assert cert.quantity == 2
    assert cert.is_signed is True


def test_certificate_data_json_roundtrip():
    """Verifica la exportación e importación de JSON mediante Pydantic."""
    cert = CertificateData(
        part_number="65-52801-12",
        quantity=1,
        status_work="OVERHAULED",
        is_signed=True
    )
    json_str = cert.model_dump_json()
    assert "65-52801-12" in json_str
    
    reconstructed = CertificateData.model_validate_json(json_str)
    assert reconstructed.part_number == cert.part_number
    assert reconstructed.status_work == "OVERHAULED"


def test_mock_extractor_with_synthetic_pdf():
    """Verifica que el extractor Mock lea correctamente los datos de un PDF sintético."""
    pdf_path = CERTIFICATES_DIR / "cert_01_ok_panel.pdf"
    assert pdf_path.exists(), "El PDF cert_01_ok_panel.pdf no existe."

    extractor = MockCertificateExtractor()
    cert_data = extractor.extract(pdf_path)

    assert isinstance(cert_data, CertificateData)
    assert cert_data.part_number == "139-00-854-22NK"
    assert cert_data.quantity == 16
    assert cert_data.status_work == "NEW"
    assert cert_data.is_signed is True
    assert cert_data.authorized_name == "V. Martinez"


def test_gemini_extractor_without_key_raises_error():
    """Verifica que GeminiCertificateExtractor lance un error claro si la API Key no está configurada."""
    with pytest.raises(ValueError) as excinfo:
        GeminiCertificateExtractor(api_key="tu_api_key_aqui")
    assert "No se encontró una clave válida de Gemini API" in str(excinfo.value)
