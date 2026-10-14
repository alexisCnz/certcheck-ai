"""
CertCheck AI - Aplicación Web Principal (Streamlit)
Validador Inteligente de Conformidad entre Certificados de Aeronavegabilidad (FAA 8130-3) y Órdenes de Compra (PO).
"""

import os
import json
import tempfile
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

# Configuración de página de Streamlit (debe ser la primera llamada de Streamlit)
st.set_page_config(
    page_title="CertCheck AI | Aeronautical Conformity",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

from src.config import DATA_DIR, CERTIFICATES_DIR, ORDERS_DIR, GEMINI_API_KEY, validate_config
from src.extractor.schemas import CertificateData
from src.extractor.mock_extractor import MockCertificateExtractor
from src.validator.models import (
    PurchaseOrderInput,
    ValidationStatus,
    AlertSeverity
)
from src.validator.engine import ConformityValidatorEngine

# Import condicional de Gemini para evitar caídas si no hay credenciales
try:
    from src.extractor.gemini_extractor import GeminiCertificateExtractor
    GEMINI_AVAILABLE = True
except Exception:
    GEMINI_AVAILABLE = False


# ==============================================================================
# ESTILOS CSS PERSONALIZADOS (Aviation Clean Dark/Light)
# ==============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .status-card-pass {
        background-color: #ECFDF5;
        border-left: 6px solid #10B981;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .status-card-review {
        background-color: #FFFBEB;
        border-left: 6px solid #F59E0B;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .status-card-fail {
        background-color: #FEF2F2;
        border-left: 6px solid #EF4444;
        padding: 1.2rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    .metric-box {
        background: #F9FAFB;
        border: 1px solid #E5E7EB;
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    .badge-critical {
        background-color: #FEE2E2;
        color: #991B1B;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .badge-warning {
        background-color: #FEF3C7;
        color: #92400E;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
    .badge-info {
        background-color: #DBEAFE;
        color: #1E40AF;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# ==============================================================================
# CARGA DE DATOS DE EJEMPLO
# ==============================================================================
@st.cache_data
def load_po_database():
    """Carga el catálogo de órdenes de compra sintéticas."""
    csv_path = ORDERS_DIR / "purchase_orders.csv"
    if csv_path.exists():
        return pd.read_csv(csv_path)
    return pd.DataFrame()


@st.cache_data
def load_ground_truth():
    """Carga el Ground Truth de los 20 certificados sintéticos."""
    gt_path = DATA_DIR / "ground_truth.json"
    if gt_path.exists():
        with open(gt_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


# ==============================================================================
# BARRA LATERAL (Sidebar)
# ==============================================================================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/airplane-mode-on.png", width=64)
    st.title("CertCheck AI ✈️")
    st.caption("Aeronautical Supply Chain Quarantine Assistant")

    st.markdown("---")
    st.subheader("⚙️ Configuración del Motor")

    has_api_key = validate_config()
    engine_mode = st.radio(
        "Modo de Extracción Documental:",
        options=["🤖 Google Gemini (LLM)", "⚡ Modo Demo / Sintético (Offline)"],
        index=0 if has_api_key else 1,
        help="El modo Gemini utiliza IA multimodal. El modo Demo usa el repositorio local sintético sin costo ni API key."
    )

    if engine_mode == "🤖 Google Gemini (LLM)":
        if not has_api_key:
            user_key_input = st.text_input("Ingresa tu Gemini API Key:", type="password")
            if user_key_input:
                os.environ["GEMINI_API_KEY"] = user_key_input
                st.success("API Key cargada temporalmente.")
            else:
                st.warning("⚠️ Sin API Key configurada. Puedes obtener una gratis en Google AI Studio o usar el 'Modo Demo'.")
        else:
            st.success("✅ Gemini API Key detectada en entorno.")

    st.markdown("---")
    st.subheader("🧪 Carga Rápida de Casos de Prueba")
    st.caption("Selecciona uno de los 20 casos sintéticos para poblar la pantalla al instante:")

    gt_data = load_ground_truth()
    case_options = ["-- Cargar caso manual --"] + [
        f"{c['case_id']}: {c['po_number']} - {c['description'][:22]} ({'OK' if c['is_ok'] else 'ERR: ' + c['error_type']})"
        for c in gt_data
    ]
    selected_case_label = st.selectbox("Casos preconfigurados:", case_options)

    st.markdown("---")
    st.markdown(
        """
        **Estándares soportados:**
        - FAA Form 8130-3 (Rev. 02-14)
        - EASA Form 1 (Compatible)
        - Regulación: 14 CFR Part 43 / 21
        """
    )


# ==============================================================================
# CUERPO PRINCIPAL (Header y Formulario de Entrada)
# ==============================================================================
st.markdown('<div class="main-header">CertCheck AI ✈️🔍</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Cotejo automatizado entre Certificados de Aeronavegabilidad (FAA 8130-3) y Órdenes de Compra (PO)</div>',
    unsafe_allow_html=True
)

# Inicializar valores por defecto de la PO
default_po = ""
default_pn = ""
default_qty = None
default_cond = "NEW"
default_sn = ""
selected_pdf_path = None

if selected_case_label != "-- Cargar caso manual --":
    case_idx = case_options.index(selected_case_label) - 1
    case_obj = gt_data[case_idx]
    default_po = case_obj["po_number"]
    default_pn = case_obj["expected_pn"]
    default_qty = case_obj["expected_qty"]
    default_cond = case_obj["expected_condition"]
    default_sn = case_obj["expected_sn"]
    selected_pdf_path = CERTIFICATES_DIR / case_obj["file_name"]

# Layout en dos columnas: Entrada de PO y Carga del Certificado
col_po, col_cert = st.columns([1, 1], gap="large")

with col_po:
    st.markdown("### 📋 1. Datos de la Orden de Compra (PO)")
    st.caption("Ingresa la información pactada en tu sistema de compras/ERP:")

    po_number_input = st.text_input(
        "Número de PO *",
        value=default_po,
        placeholder="ej: PO-2026-1001"
    )
    expected_pn_input = st.text_input(
        "Part Number Esperado (P/N) *",
        value=default_pn,
        placeholder="ej: 139-00-854-22NK"
    )

    with st.expander("➕ Especificaciones Adicionales de la PO (Opcional)"):
        expected_qty_input = st.number_input(
            "Cantidad esperada:",
            min_value=1,
            value=int(default_qty) if default_qty else 1,
            step=1
        )
        expected_cond_input = st.selectbox(
            "Condición requerida:",
            options=["NEW", "OVERHAULED", "REPAIRED", "INSPECTED/TESTED", "MODIFIED"],
            index=["NEW", "OVERHAULED", "REPAIRED", "INSPECTED/TESTED", "MODIFIED"].index(default_cond) if default_cond in ["NEW", "OVERHAULED", "REPAIRED", "INSPECTED/TESTED", "MODIFIED"] else 0
        )
        expected_sn_input = st.text_input(
            "Serial Number esperado (si aplica):",
            value=default_sn if default_sn and default_sn != "N/A" else "",
            placeholder="ej: SN-84902-B o dejar vacío"
        )

with col_cert:
    st.markdown("### 📄 2. Certificado de Aeronavegabilidad (PDF)")
    st.caption("Carga el certificado digital o escaneado recibido en cuarentena:")

    uploaded_pdf = st.file_uploader(
        "Subir archivo PDF (FAA 8130-3)",
        type=["pdf"],
        help="Arrastra o selecciona el certificado emitido por el fabricante o taller MRO."
    )

    if uploaded_pdf is not None:
        st.success(f"Archivo cargado: **{uploaded_pdf.name}** ({uploaded_pdf.size / 1024:.1f} KB)")
    elif selected_pdf_path and selected_pdf_path.exists():
        st.info(f"Usando certificado de prueba: **{selected_pdf_path.name}**")


# ==============================================================================
# BOTÓN DE ANÁLISIS Y EJECUCIÓN
# ==============================================================================
st.markdown("<br>", unsafe_allow_html=True)
validate_btn = st.button("🚀 Ejecutar Verificación de Conformidad", type="primary", use_container_width=True)

if validate_btn:
    if not po_number_input or not expected_pn_input:
        st.error("⚠️ Por favor completa al menos el **Número de PO** y el **Part Number Esperado** antes de validar.")
    elif uploaded_pdf is None and (not selected_pdf_path or not selected_pdf_path.exists()):
        st.error("⚠️ Por favor sube un archivo PDF o selecciona un caso de prueba.")
    else:
        # 1. Preparar archivo PDF
        temp_pdf_path = None
        if uploaded_pdf is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_pdf.read())
                temp_pdf_path = Path(tmp.name)
            target_pdf_path = temp_pdf_path
        else:
            target_pdf_path = selected_pdf_path

        # 2. Extracción de datos
        with st.spinner("🔍 Analizando documento y extrayendo bloques aeronáuticos..."):
            cert_data = None
            try:
                if engine_mode == "🤖 Google Gemini (LLM)" and GEMINI_AVAILABLE and os.getenv("GEMINI_API_KEY"):
                    extractor = GeminiCertificateExtractor()
                    cert_data = extractor.extract(target_pdf_path)
                else:
                    extractor = MockCertificateExtractor()
                    cert_data = extractor.extract(target_pdf_path)
            except Exception as e:
                st.error(f"❌ Error durante la extracción documental: {e}")
                if "API Key" in str(e) or "403" in str(e):
                    st.info("💡 Puedes conmutar a 'Modo Demo / Sintético' en la barra lateral para probar sin API Key.")

        # Limpiar archivo temporal si aplica
        if temp_pdf_path and temp_pdf_path.exists():
            try:
                os.remove(temp_pdf_path)
            except Exception:
                pass

        # 3. Validación Determinística
        if cert_data:
            po_input = PurchaseOrderInput(
                po_number=po_number_input.strip(),
                expected_pn=expected_pn_input.strip(),
                expected_qty=expected_qty_input,
                expected_condition=expected_cond_input,
                expected_sn=expected_sn_input.strip() if expected_sn_input else None
            )

            # Usamos fecha de referencia 2026 para testing consistente del dataset sintético
            engine = ConformityValidatorEngine(reference_date=datetime(2026, 4, 1))
            report = engine.validate(cert_data, po_input)

            st.markdown("---")
            st.markdown("## 📊 Resultado de la Evaluación")

            # Banner de Semáforo
            if report.status == ValidationStatus.PASS:
                st.markdown(
                    f"""
                    <div class="status-card-pass">
                        <h2 style="color: #065F46; margin:0;">🟢 CONFORME / APROBADO</h2>
                        <p style="color: #047857; margin-top: 6px; font-size: 1.05rem;">{report.summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            elif report.status == ValidationStatus.REVIEW:
                st.markdown(
                    f"""
                    <div class="status-card-review">
                        <h2 style="color: #92400E; margin:0;">🟡 REVISIÓN REQUERIDA</h2>
                        <p style="color: #B45309; margin-top: 6px; font-size: 1.05rem;">{report.summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f"""
                    <div class="status-card-fail">
                        <h2 style="color: #991B1B; margin:0;">🔴 RECHAZADO / CUARENTENA</h2>
                        <p style="color: #B91C1C; margin-top: 6px; font-size: 1.05rem;">{report.summary}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Lista de Alertas / Discrepancias
            st.markdown("### 🚨 Detalle de Discrepancias y Alertas")
            if not report.alerts:
                st.success("✅ No se detectaron discrepancias. Todos los campos concuerdan con la orden de compra y la regulación.")
            else:
                for alert in report.alerts:
                    badge_class = (
                        "badge-critical" if alert.severity == AlertSeverity.CRITICAL
                        else "badge-warning" if alert.severity == AlertSeverity.WARNING
                        else "badge-info"
                    )
                    st.markdown(
                        f"""
                        <div style="background: white; border: 1px solid #E5E7EB; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                            <span class="{badge_class}">{alert.severity.value}</span>
                            <strong style="margin-left: 8px; color: #1F2937;">[{alert.code}]</strong> 
                            <span style="color: #4B5563;">Campo: <code>{alert.field}</code></span>
                            <div style="margin-top: 6px; color: #374151;">{alert.message}</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            # Comparativa Detallada: PO vs Certificado 8130-3
            st.markdown("### 📑 Comparativa Detallada: PO vs. Certificado 8130-3")
            
            comparison_rows = [
                {"Bloque": "Bloque 8", "Parámetro": "Part Number (P/N)", "Esperado en PO": po_input.expected_pn, "Certificado 8130-3": cert_data.part_number, "Estado": "✅ Coincide" if po_input.expected_pn.upper() == cert_data.part_number.upper() else "❌ Discrepante"},
                {"Bloque": "Bloque 9", "Parámetro": "Cantidad", "Esperado en PO": str(po_input.expected_qty) if po_input.expected_qty else "N/A", "Certificado 8130-3": str(cert_data.quantity), "Estado": "✅ Coincide" if (not po_input.expected_qty or po_input.expected_qty == cert_data.quantity) else "⚠️ Cantidad distinta"},
                {"Bloque": "Bloque 10", "Parámetro": "Serial / Batch Number", "Esperado en PO": po_input.expected_sn or "N/A", "Certificado 8130-3": cert_data.serial_number or "N/A", "Estado": "✅ Conforme" if (not po_input.expected_sn or po_input.expected_sn == cert_data.serial_number) else "⚠️ Revisar serial"},
                {"Bloque": "Bloque 11", "Parámetro": "Condición / Estado", "Esperado en PO": po_input.expected_condition or "N/A", "Certificado 8130-3": cert_data.status_work, "Estado": "✅ Conforme" if (not po_input.expected_condition or po_input.expected_condition in cert_data.status_work) else "❌ Condición distinta"},
                {"Bloque": "Bloque 3", "Parámetro": "Form Tracking Number", "Esperado en PO": "Trazabilidad documental", "Certificado 8130-3": cert_data.form_tracking_number or "VACÍO", "Estado": "✅ Presente" if cert_data.form_tracking_number else "⚠️ Faltante"},
                {"Bloque": "Bloque 4", "Parámetro": "Organización Emisora", "Esperado en PO": "Proveedor / OEM calificado", "Certificado 8130-3": f"{cert_data.organization_name or 'N/A'}", "Estado": "✅ Identificado"},
                {"Bloque": "Bloque 5", "Parámetro": "Nexo (PO/WO/Invoice)", "Esperado en PO": po_input.po_number, "Certificado 8130-3": cert_data.work_order_po or "N/A", "Estado": "ℹ️ Referenciado"},
                {"Bloque": "Bloque 12", "Parámetro": "Shelf Life / Caducidad", "Esperado en PO": "Vigente", "Certificado 8130-3": cert_data.shelf_life_expiry or "No aplica", "Estado": "❌ VENCIDO" if any(a.code == "ERR_SHELF_LIFE_EXPIRED" for a in report.alerts) else "✅ Vigente"},
                {"Bloque": "Bloque 13/14", "Parámetro": "Firma Autorizada y Fecha", "Esperado en PO": "Firma válida obligatoria", "Certificado 8130-3": f"{cert_data.authorized_name or 'SIN FIRMA'} ({cert_data.signature_date or 'SIN FECHA'})", "Estado": "✅ Válida" if cert_data.is_signed else "❌ FIRMA FALTANTE"}
            ]

            st.dataframe(pd.DataFrame(comparison_rows), use_container_width=True, hide_index=True)

            # Exportación de Datos
            st.markdown("### 💾 Exportar Reporte de Conformidad")
            col_json, col_csv = st.columns(2)

            with col_json:
                json_data = report.model_dump_json(indent=2)
                st.download_button(
                    label="📥 Descargar Reporte Completo (JSON)",
                    data=json_data,
                    file_name=f"report_{po_input.po_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                    use_container_width=True
                )

            with col_csv:
                # Aplanar para CSV
                csv_record = {
                    "po_number": po_input.po_number,
                    "expected_pn": po_input.expected_pn,
                    "certified_pn": cert_data.part_number,
                    "status": report.status.value,
                    "traffic_light": report.traffic_light,
                    "alerts_count": len(report.alerts),
                    "alert_codes": "; ".join([a.code for a in report.alerts]),
                    "tracking_number": cert_data.form_tracking_number,
                    "organization": cert_data.organization_name,
                    "evaluated_at": report.evaluated_at
                }
                csv_df = pd.DataFrame([csv_record])
                csv_data = csv_df.to_csv(index=False)
                st.download_button(
                    label="📥 Descargar Resumen de Calidad (CSV)",
                    data=csv_data,
                    file_name=f"summary_{po_input.po_number}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
