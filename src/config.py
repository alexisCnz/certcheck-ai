import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env en la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# Clave de API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Modelo de LLM predeterminado
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Rutas estándar del proyecto
DATA_DIR = BASE_DIR / "data"
CERTIFICATES_DIR = DATA_DIR / "certificates"
ORDERS_DIR = DATA_DIR / "orders"

def validate_config() -> bool:
    """
    Verifica que la configuración esencial esté presente.
    Retorna True si la API key está configurada, False de lo contrario.
    """
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != "tu_api_key_aqui")
