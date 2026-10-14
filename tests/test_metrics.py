"""
Pruebas automatizadas de rendimiento y métricas del sistema CertCheck AI.
Garantiza que el sistema cumpla con los estándares mínimos de calidad industrial:
- Accuracy >= 95%
- Recall == 100% (cero material defectuoso liberado a bodega / falso negativo)
"""

from scripts.evaluate_metrics import run_benchmark


def test_system_performance_metrics():
    """Verifica que el benchmark cumpla con los SLAs de calidad industrial."""
    report = run_benchmark()
    metrics = report["metrics"]
    conf_matrix = report["confusion_matrix"]

    # En aviación comercial no se tolera ningún falso negativo (liberar pieza defectuosa)
    assert conf_matrix["false_negatives"] == 0, (
        f"CRÍTICO: Se encontraron {conf_matrix['false_negatives']} falsos negativos."
    )
    assert metrics["recall_sensitivity"] == 1.0, "El Recall debe ser 100%."
    assert metrics["accuracy"] >= 0.95, f"La exactitud ({metrics['accuracy']:.2%}) debe superar el 95%."
    assert metrics["precision"] >= 0.95, f"La precisión ({metrics['precision']:.2%}) debe superar el 95%."
