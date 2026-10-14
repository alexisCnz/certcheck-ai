"""
Implementación del extractor de certificados aeronáuticos utilizando el SDK oficial google-genai.
Soporta salida estructurada con Pydantic, extracción digital con pdfplumber y procesamiento multimodal nativo de PDFs.
"""

from pathlib import Path
from typing import Optional
import pdfplumber
from google import genai
from google.genai import types

from src.config import GEMINI_API_KEY, GEMINI_MODEL
from src.extractor.base import BaseCertificateExtractor
from src.extractor.schemas import CertificateData
from src.extractor.prompts import SYSTEM_PROMPT, EXTRACTION_USER_PROMPT


class GeminiCertificateExtractor(BaseCertificateExtractor):
    """
    Extractor de certificados basado en la API moderna de Google Gemini (google-genai).
    Garantiza salidas estructuradas conformes al esquema CertificateData de Pydantic.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = model_name or GEMINI_MODEL

        if not self.api_key or self.api_key == "tu_api_key_aqui":
            raise ValueError(
                "No se encontró una clave válida de Gemini API. "
                "Configura GEMINI_API_KEY en tu archivo .env o pásala al constructor."
            )

        # Inicializar el cliente oficial moderno de Google GenAI
        self.client = genai.Client(api_key=self.api_key)

    def _extract_text_with_pdfplumber(self, pdf_path: Path) -> str:
        """Intenta extraer texto vectorial digital del PDF."""
        extracted_text = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        extracted_text.append(f"--- PÁGINA {page_idx + 1} ---\n{text}")
        except Exception as e:
            print(f"Aviso: pdfplumber no pudo leer texto del PDF ({e}). Se usará modo multimodal.")
        
        return "\n".join(extracted_text).strip()

    def extract(self, pdf_path: Path) -> CertificateData:
        """
        Extrae datos estructurados del certificado PDF.
        Estrategia híbrida:
        1. Si el PDF tiene texto digital (>50 caracteres), envía el texto al LLM.
        2. Si es escaneado o imagen, envía los bytes directos del PDF como payload multimodal.
        """
        if not pdf_path.exists():
            raise FileNotFoundError(f"El archivo PDF no existe en la ruta: {pdf_path}")

        contents = []
        digital_text = self._extract_text_with_pdfplumber(pdf_path)

        if len(digital_text) > 50:
            prompt = EXTRACTION_USER_PROMPT.format(document_content=digital_text)
            contents.append(prompt)
        else:
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()
            contents.append(
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")
            )
            contents.append(
                "Extrae minuciosamente todos los campos de este certificado aeronáutico conforme al esquema requerido."
            )

        # Configuración de generación estructurada con esquema Pydantic
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=CertificateData,
            temperature=0.0  # Máximo determinismo
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=contents,
            config=config
        )

        raw_json_str = response.text.strip()
        try:
            return CertificateData.model_validate_json(raw_json_str)
        except Exception:
            cleaned = raw_json_str.replace("```json", "").replace("```", "").strip()
            return CertificateData.model_validate_json(cleaned)
