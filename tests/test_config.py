from src.config import BASE_DIR, DATA_DIR, CERTIFICATES_DIR, ORDERS_DIR

def test_project_paths_exist():
    """Verifica que las rutas base del proyecto y los directorios de datos estén definidos."""
    assert BASE_DIR.exists()
    assert DATA_DIR.exists()
    assert CERTIFICATES_DIR.exists()
    assert ORDERS_DIR.exists()
