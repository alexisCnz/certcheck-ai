# CertCheck AI ✈️🔍

> **Automated Airworthiness Certificate & Purchase Order Conformity Validator**  
> *Validador automatizado de conformidad entre certificados de aeronavegabilidad y órdenes de compra.*

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B.svg)](https://streamlit.io/)
[![Pydantic v2](https://img.shields.io/badge/Pydantic-v2-E92063.svg)](https://docs.pydantic.dev/)
[![Google Gemini](https://img.shields.io/badge/LLM-Google%20Gemini-orange.svg)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🇬🇧 English

### What is it?

**CertCheck AI** is an intelligent web application designed for aeronautical **MRO supply chain** quarantine and receiving inspection. It automates the verification between airworthiness release certificates (**FAA Form 8130-3**) and Purchase Order (PO) requirements — a process that today is done manually and is highly prone to human error.

### The Problem it Solves

In aviation receiving inspection, a single mismatched character in a Part Number, an expired shelf-life elastomer, or a certificate missing an authorized signature can ground an aircraft (AOG) or trigger a major regulatory finding.

This tool catches those discrepancies automatically, in seconds.

### Core Architecture Principle

```
[ PDF Certificate ] + [ PO Data ]
        ↓
  STAGE 1 → Google Gemini (LLM)
             Reads and extracts structured data only.
             Does NOT make compliance decisions.
        ↓
  STAGE 2 → Python Rules Engine (deterministic)
             Mathematical rules decide Pass / Review / Reject.
        ↓
  STAGE 3 → Streamlit Interface
             🟢 PASS | 🟡 REVIEW | 🔴 REJECT
```

> **Key design decision:** LLMs are probabilistic and can hallucinate. In safety-critical industries, the AI extracts data — Python decides compliance.

### Features

- 📄 **Hybrid PDF Processing:** Digital text via `pdfplumber` + scanned documents via Gemini Vision (no Tesseract required).
- 🤖 **Structured LLM Extraction:** Gemini outputs are validated against a strict Pydantic v2 schema (all 8130-3 blocks: 3, 4, 5, 8, 9, 10, 11, 12, 13/14).
- ⚖️ **Deterministic Validation Rules:**
  - Part Number divergence (Levenshtein distance for suffix/digit changes).
  - Serial number typo detection (visual substitution: `O` vs `0`, `I` vs `1`).
  - Quantity and condition mismatch.
  - Traceability / missing signature in Block 13/14.
  - Shelf Life expiration calculation from Block 12 remarks.
- 🚦 **Traffic Light Verdict:** PASS 🟢 / REVIEW 🟡 / REJECT 🔴 with per-field alert breakdown.
- 💾 **Audit Export:** Download compliance report as JSON or CSV.
- 📊 **System Metrics Panel:** Accuracy, Recall, Precision and F1-Score on 20 synthetic test cases.
- ⚡ **Demo Mode:** Works fully offline with 20 pre-loaded synthetic 8130-3 certificates — no API key needed.

### Tech Stack

| Technology | Role |
|---|---|
| Python 3.11+ | Core language |
| Streamlit | Web UI |
| Google Gemini (`google-genai`) | Multimodal document extraction |
| Pydantic v2 | JSON schema validation |
| pdfplumber | Digital PDF text extraction |
| Levenshtein | String similarity algorithm |
| ReportLab | Synthetic PDF generation |
| pandas | Data handling and CSV export |
| pytest | Automated testing (16 tests) |

### Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/certcheck-ai.git
cd certcheck-ai

# 2. Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and add your Gemini API key (free at https://aistudio.google.com/app/apikey)

# 5. Generate synthetic test dataset
python scripts/generate_dataset.py

# 6. (Optional) Run system benchmark
python scripts/evaluate_metrics.py

# 7. Launch the app
streamlit run app.py
```

### Run Tests

```bash
pytest -v
```

> Expected: **15 passed** across config, dataset, extractor and validator tests.

### System Performance (Synthetic Dataset)

| Metric | Result |
|---|---|
| Accuracy | 100% |
| Recall / Sensitivity | **100%** (0 defective parts passed through) |
| Precision | 100% |
| F1-Score | 100% |
| False Negatives | **0** (most critical metric in aviation) |

> *Note: Metrics are computed on 20 synthetic FAA 8130-3 certificates using the deterministic Mock Extractor. Real-world accuracy with the Gemini extractor depends on document scan quality.*

### Project Structure

```
certcheck-ai/
├── app.py                        ← Streamlit web app (entry point)
├── requirements.txt
├── .env.example                  ← API key template (never commit .env)
├── .gitignore
├── src/
│   ├── config.py                 ← Centralized configuration
│   ├── extractor/
│   │   ├── schemas.py            ← Pydantic CertificateData model
│   │   ├── prompts.py            ← Aerospace-specialized LLM prompts
│   │   ├── base.py               ← Abstract extractor interface
│   │   ├── gemini_extractor.py   ← Google Gemini implementation
│   │   └── mock_extractor.py     ← Offline test extractor
│   └── validator/
│       ├── models.py             ← Alert, severity and report models
│       ├── rules.py              ← 6 deterministic validation rules
│       └── engine.py             ← Conformity validator orchestrator
├── scripts/
│   ├── generate_dataset.py       ← Synthetic 8130-3 PDF generator
│   └── evaluate_metrics.py       ← System benchmark
├── data/
│   ├── certificates/             ← 20 synthetic test PDFs
│   ├── orders/purchase_orders.csv
│   ├── ground_truth.json
│   └── metrics_report.json
└── tests/                        ← 15 pytest unit tests
```

### Roadmap (v2.0)

- [ ] EASA Form 1 support (different block layout)
- [ ] Mandatory Dual Release validation (FAA + EASA)
- [ ] Minimum remaining Shelf Life rule (configurable %)
- [ ] Approved Vendor List (AVL) cross-check
- [ ] Airworthiness Directive (AD) compliance check in Block 12
- [ ] Back-to-Birth traceability verification

### Important Notes

- **No real documents:** This project uses 100% synthetic data. Never upload or process real company documents.
- **API key security:** The Gemini API key is loaded exclusively from environment variables. It is never hardcoded.
- **AI does not decide compliance:** The LLM is limited to data extraction. All compliance decisions are made by deterministic Python rules.

---

## 🇪🇸 Español

### ¿Qué es?

**CertCheck AI** es una aplicación web inteligente diseñada para el área de cuarentena e inspección de recepción en la **cadena de suministro aeronáutico (MRO)**. Automatiza la verificación entre certificados de aeronavegabilidad (**FAA Form 8130-3**) y los requerimientos de la Orden de Compra (PO).

### El Problema que Resuelve

En la recepción aeronáutica, un solo carácter incorrecto en un Part Number, un sellante con Shelf Life vencido o un certificado sin firma autorizada puede dejar un avión en tierra (AOG) o generar un hallazgo regulatorio mayor.

Esta herramienta detecta esas discrepancias automáticamente, en segundos.

### Principio de Arquitectura

```
[ Certificado PDF ] + [ Datos de la PO ]
        ↓
  ETAPA 1 → Google Gemini (LLM)
             Lee y extrae datos estructurados únicamente.
             NO toma decisiones de conformidad.
        ↓
  ETAPA 2 → Motor de Reglas Python (determinístico)
             Reglas matemáticas deciden Aprobado / Revisar / Rechazado.
        ↓
  ETAPA 3 → Interfaz Streamlit
             🟢 CONFORME | 🟡 REVISIÓN | 🔴 RECHAZAR
```

### Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/certcheck-ai.git
cd certcheck-ai

# 2. Crear y activar el entorno virtual
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env y agrega tu API Key de Gemini (gratis en https://aistudio.google.com/app/apikey)

# 5. Generar el dataset sintético de prueba
python scripts\generate_dataset.py

# 6. Lanzar la app
streamlit run app.py
```

### Notas Importantes

- **Solo datos sintéticos:** Este proyecto usa exclusivamente datos ficticios. Nunca proceses documentos reales de tu empresa.
- **Seguridad de API key:** La clave de Gemini se carga desde variables de entorno. Nunca está en el código.
- **La IA no decide conformidad:** El LLM se limita a extraer datos. Las decisiones de conformidad son tomadas por reglas determinísticas en Python.

---

## Author / Autor

Built as a portfolio project combining aeronautical MRO domain expertise with applied AI engineering.  
*Construido como proyecto de portafolio combinando experiencia en MRO aeronáutico con ingeniería de IA aplicada.*

---

## License / Licencia

This project is licensed under the MIT License.
