# CertCheck AI ✈️🔍

> **Automated Airworthiness Certificate & Purchase Order Conformity Validator**  
> *Validador automatizado de conformidad entre certificados de aeronavegabilidad y órdenes de compra.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange.svg)](https://ai.google.dev/)

---

## English

### Overview
**CertCheck AI** is an intelligent assistant designed for aeronautical supply chain (MRO) quarantine and receiving inspection. It automates the verification between airworthiness release certificates (FAA Form 8130-3 / EASA Form 1) and Purchase Order (PO) requirements.

### Architecture Principle
- **Probabilistic LLM for Extraction**: Multimodal document processing to extract structured data into strict Pydantic models.
- **Deterministic Engine for Validation**: 100% reliable Python business rules to detect Part Number discrepancies, typos, condition mismatch, and shelf-life expiration. LLMs do not decide compliance in regulated environments.

---

## Español

### Descripción General
**CertCheck AI** es un asistente inteligente diseñado para el área de cuarentena e inspección de recepción en la cadena de suministro aeronáutico (MRO). Automatiza la verificación entre certificados de aeronavegabilidad (FAA 8130-3 / EASA Form 1) y los requerimientos de la Orden de Compra (PO).

### Principio de Arquitectura
- **LLM probabilístico para extracción**: Procesa documentos multimodales para extraer datos estructurados validados con modelos estrictos de Pydantic.
- **Motor determinístico para validación**: Reglas de negocio en Python puro para detectar divergencias de Part Number, errores tipográficos en seriales, discrepancias de cantidad/condición y vencimiento de shelf life. La IA nunca decide por sí sola el pase/rechazo en un entorno regulado.

---

## Project Structure / Estructura del Proyecto

```text
certcheck-ai/
├── src/
│   ├── extractor/        # Extracción multimodal con Gemini + Pydantic
│   ├── validator/        # Motor de reglas determinísticas (Python)
│   ├── ui/               # Interfaz web en Streamlit
│   └── config.py         # Configuración central y variables de entorno
├── data/
│   ├── certificates/     # PDFs sintéticos de prueba
│   └── orders/           # Órdenes de compra sintéticas
├── tests/                # Pruebas unitarias automatizadas con pytest
├── .env.example          # Plantilla de variables de entorno
├── .gitignore            # Archivos y secretos ignorados
└── requirements.txt      # Dependencias del proyecto
```
