"""
Módulo de extracción de certificados aeronáuticos.
"""

from src.extractor.schemas import CertificateData
from src.extractor.base import BaseCertificateExtractor
from src.extractor.mock_extractor import MockCertificateExtractor

__all__ = [
    "CertificateData",
    "BaseCertificateExtractor",
    "MockCertificateExtractor",
]

# Importación condicional del extractor de Gemini
try:
    from src.extractor.gemini_extractor import GeminiCertificateExtractor
    __all__.append("GeminiCertificateExtractor")
except ImportError:
    pass
