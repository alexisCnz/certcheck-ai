"""
Interfaz base abstracta para los extractores de certificados.
Permite intercambiar el proveedor de LLM (Gemini, OpenAI, Anthropic, Ollama local, etc.)
sin modificar el resto de la aplicación.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from src.extractor.schemas import CertificateData


class BaseCertificateExtractor(ABC):
    """Clase base abstracta que define el contrato de cualquier extractor documental."""

    @abstractmethod
    def extract(self, pdf_path: Path) -> CertificateData:
        """
        Procesa un archivo PDF de certificado aeronáutico y extrae sus datos estructurados.
        
        Args:
            pdf_path: Ruta al archivo PDF en el sistema de archivos.
            
        Returns:
            CertificateData: Objeto validado por Pydantic con la información extraída.
        """
        pass
