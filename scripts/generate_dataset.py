"""
Script para generar el dataset sintético de CertCheck AI:
- 20 Certificados en formato PDF que imitan el estándar FAA Form 8130-3 (Rev. 02-14)
- 1 Archivo CSV con las Órdenes de Compra (PO)
- 1 Archivo JSON de Ground Truth con la verdad fundamental para métricas
"""

import json
import csv
from pathlib import Path
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CERTS_DIR = DATA_DIR / "certificates"
ORDERS_DIR = DATA_DIR / "orders"

CERTS_DIR.mkdir(parents=True, exist_ok=True)
ORDERS_DIR.mkdir(parents=True, exist_ok=True)

# 20 Casos Sintéticos Aeronáuticos (12 OK y 8 con errores típicos de cuarentena)
CASES = [
    {
        "case_id": "CERT-01",
        "file_name": "cert_01_ok_panel.pdf",
        "po_number": "PO-2026-1001",
        "expected_pn": "139-00-854-22NK",
        "expected_qty": 16,
        "expected_condition": "NEW",
        "expected_sn": "N/A",
        # Datos del Certificado 8130-3
        "tracking_no": "US-FAA-7818-01",
        "org_name": "AeroSynthetic Seating Systems LLC",
        "org_address": "1200 Aviation Parkway, Fort Worth, TX 76177",
        "work_order_po": "PO-2026-1001 / WO-4401",
        "item": "1",
        "description": "PANEL ARMREST CTR RH",
        "cert_pn": "139-00-854-22NK",
        "cert_qty": 16,
        "cert_sn": "N/A",
        "cert_status": "NEW",
        "remarks": "Subcomponents of TSO-C127a authorization. Standard commercial packaging.",
        "cert_type": "13",  # 13: Manufacturing / New
        "auth_name": "V. Martinez",
        "auth_no": "DMIR-778841",
        "auth_date": "14-MAR-2026",
        # Ground Truth
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Todos los datos coinciden exactamente con la PO."
    },
    {
        "case_id": "CERT-02",
        "file_name": "cert_02_ok_actuator.pdf",
        "po_number": "PO-2026-1002",
        "expected_pn": "65-52801-12",
        "expected_qty": 1,
        "expected_condition": "OVERHAULED",
        "expected_sn": "SN-ACT-9821",
        "tracking_no": "US-FAA-7818-02",
        "org_name": "SkyTech MRO Component Services Inc.",
        "org_address": "8500 Maintenance Way, Miami, FL 33142",
        "work_order_po": "PO-2026-1002 / WO-9821",
        "item": "1",
        "description": "MAIN GEAR ACTUATOR CYLINDER",
        "cert_pn": "65-52801-12",
        "cert_qty": 1,
        "cert_sn": "SN-ACT-9821",
        "cert_status": "OVERHAULED",
        "remarks": "Overhauled in accordance with CMM 32-10-45 Rev 12. Dual release FAA/EASA.",
        "cert_type": "14",  # 14: Return to Service
        "auth_name": "J. Reynolds",
        "auth_no": "FAA-CRS-SK4R91",
        "auth_date": "10-FEB-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Overhaul documentado y serial coincidente."
    },
    {
        "case_id": "CERT-03",
        "file_name": "cert_03_err_pn_divergent.pdf",
        "po_number": "PO-2026-1003",
        "expected_pn": "139-00-854-22NK",
        "expected_qty": 16,
        "expected_condition": "NEW",
        "expected_sn": "N/A",
        "tracking_no": "US-FAA-7818-03",
        "org_name": "AeroSynthetic Seating Systems LLC",
        "org_address": "1200 Aviation Parkway, Fort Worth, TX 76177",
        "work_order_po": "PO-2026-1003",
        "item": "1",
        "description": "PANEL ARMREST CTR RH",
        # ERROR: Sufijo cambiado NK -> NL
        "cert_pn": "139-00-854-22NL",
        "cert_qty": 16,
        "cert_sn": "N/A",
        "cert_status": "NEW",
        "remarks": "Manufactured to approved design data.",
        "cert_type": "13",
        "auth_name": "V. Martinez",
        "auth_no": "DMIR-778841",
        "auth_date": "15-MAR-2026",
        "is_ok": False,
        "error_type": "PN_DIVERGENCE",
        "explanation": "Rechazar: PN divergente. Se solicitó 139-00-854-22NK pero el certificado indica 139-00-854-22NL."
    },
    {
        "case_id": "CERT-04",
        "file_name": "cert_04_ok_fuel_flow.pdf",
        "po_number": "PO-2026-1004",
        "expected_pn": "324400-1002",
        "expected_qty": 2,
        "expected_condition": "REPAIRED",
        "expected_sn": "SN-FF-4401",
        "tracking_no": "US-FAA-7818-04",
        "org_name": "Global Fuel Instruments Repair Station",
        "org_address": "400 Turbine Blvd, Phoenix, AZ 85034",
        "work_order_po": "PO-2026-1004 / WO-3312",
        "item": "1",
        "description": "FUEL FLOW TRANSMITTER",
        "cert_pn": "324400-1002",
        "cert_qty": 2,
        "cert_sn": "SN-FF-4401",
        "cert_status": "REPAIRED",
        "remarks": "Repaired and bench tested per CMM 73-30-01. Leak check satisfactory.",
        "cert_type": "14",
        "auth_name": "R. Sterling",
        "auth_no": "FAA-CRS-GF5R12",
        "auth_date": "02-APR-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Reparación certificada y PN correspondiente."
    },
    {
        "case_id": "CERT-05",
        "file_name": "cert_05_ok_oring.pdf",
        "po_number": "PO-2026-1005",
        "expected_pn": "MS28775-224",
        "expected_qty": 50,
        "expected_condition": "NEW",
        "expected_sn": "BATCH-2026-B9",
        "tracking_no": "US-FAA-7818-05",
        "org_name": "Precision Elastomers Aerospace Corp",
        "org_address": "99 Industrial Loop, Akron, OH 44301",
        "work_order_po": "PO-2026-1005",
        "item": "1",
        "description": "PACKING PREFORMED O-RING",
        "cert_pn": "MS28775-224",
        "cert_qty": 50,
        "cert_sn": "BATCH-2026-B9",
        "cert_status": "NEW",
        "remarks": "CURE DATE: 1Q2025. SHELF LIFE: 60 MONTHS. EXPIRY DATE: 31-MAR-2030. Batch traceability maintained.",
        "cert_type": "13",
        "auth_name": "D. Miller",
        "auth_no": "DMIR-331002",
        "auth_date": "20-JAN-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Shelf life vigente (vence en 2030) y lote trazable."
    },
    {
        "case_id": "CERT-06",
        "file_name": "cert_06_err_serial_typo.pdf",
        "po_number": "PO-2026-1006",
        "expected_pn": "060-0012-00",
        "expected_qty": 1,
        "expected_condition": "OVERHAULED",
        "expected_sn": "SN-84902-B",
        "tracking_no": "US-FAA-7818-06",
        "org_name": "Avionics Support International",
        "org_address": "3100 Radar Way, Atlanta, GA 30320",
        "work_order_po": "PO-2026-1006",
        "item": "1",
        "description": "TCAS DIRECTIONAL ANTENNA",
        "cert_pn": "060-0012-00",
        "cert_qty": 1,
        # ERROR: Letra 'O' en vez del número cero '0'
        "cert_sn": "SN-849O2-B",
        "cert_status": "OVERHAULED",
        "remarks": "Overhauled per CMM 34-43-02. VSWR and phase test passed.",
        "cert_type": "14",
        "auth_name": "A. Chen",
        "auth_no": "FAA-CRS-AS9R40",
        "auth_date": "18-MAY-2026",
        "is_ok": False,
        "error_type": "SERIAL_TYPO_SUSPECT",
        "explanation": "Revisar: Serial sospechoso de error de tipeo. PO espera SN-84902-B pero el 8130 indica SN-849O2-B (letra O por número 0)."
    },
    {
        "case_id": "CERT-07",
        "file_name": "cert_07_ok_probe.pdf",
        "po_number": "PO-2026-1007",
        "expected_pn": "B31792-1",
        "expected_qty": 1,
        "expected_condition": "NEW",
        "expected_sn": "SN-PS-7719",
        "tracking_no": "US-FAA-7818-07",
        "org_name": "AeroSensor Precision Dynamics",
        "org_address": "77 Pitot Way, Seattle, WA 98108",
        "work_order_po": "PO-2026-1007",
        "item": "1",
        "description": "PITOT STATIC TUBE PROBE",
        "cert_pn": "B31792-1",
        "cert_qty": 1,
        "cert_sn": "SN-PS-7719",
        "cert_status": "NEW",
        "remarks": "Heater circuit resistance verified. Conforms to approved drawing B31792.",
        "cert_type": "13",
        "auth_name": "T. Walker",
        "auth_no": "DMIR-552190",
        "auth_date": "05-JUN-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Sensor nuevo con trazabilidad y serial idéntico."
    },
    {
        "case_id": "CERT-08",
        "file_name": "cert_08_err_qty_mismatch.pdf",
        "po_number": "PO-2026-1008",
        "expected_pn": "NAS1149F0332P",
        "expected_qty": 100,
        "expected_condition": "NEW",
        "expected_sn": "BATCH-4412",
        "tracking_no": "US-FAA-7818-08",
        "org_name": "Standard Aero Fasteners Inc.",
        "org_address": "500 Hardware Ave, Dallas, TX 75261",
        "work_order_po": "PO-2026-1008",
        "item": "1",
        "description": "WASHER FLAT AERONAUTICAL",
        "cert_pn": "NAS1149F0332P",
        # ERROR: Cantidad 80 en vez de 100
        "cert_qty": 80,
        "cert_sn": "BATCH-4412",
        "cert_status": "NEW",
        "remarks": "Standard hardware NAS specification. Chemical test certified.",
        "cert_type": "13",
        "auth_name": "M. Gomez",
        "auth_no": "DMIR-882014",
        "auth_date": "12-FEB-2026",
        "is_ok": False,
        "error_type": "QTY_MISMATCH",
        "explanation": "Revisar: Discrepancia en cantidad. PO solicita 100 unidades pero el certificado ampara solo 80."
    },
    {
        "case_id": "CERT-09",
        "file_name": "cert_09_ok_regulator.pdf",
        "po_number": "PO-2026-1009",
        "expected_pn": "4116-001",
        "expected_qty": 1,
        "expected_condition": "REPAIRED",
        "expected_sn": "SN-PR-1102",
        "tracking_no": "US-FAA-7818-09",
        "org_name": "Pneumatic Aerospace Solutions",
        "org_address": "1420 Valve St, Wichita, KS 67210",
        "work_order_po": "PO-2026-1009 / WO-7714",
        "item": "1",
        "description": "BLEED AIR PRESSURE REGULATOR",
        "cert_pn": "4116-001",
        "cert_qty": 1,
        "cert_sn": "SN-PR-1102",
        "cert_status": "REPAIRED",
        "remarks": "Diaphragm replaced. Tested per CMM 36-11-20. Satisfactory.",
        "cert_type": "14",
        "auth_name": "K. Adams",
        "auth_no": "FAA-CRS-PA4R19",
        "auth_date": "22-JAN-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Regulador reparado con trazabilidad técnica completa."
    },
    {
        "case_id": "CERT-10",
        "file_name": "cert_10_ok_brake.pdf",
        "po_number": "PO-2026-1010",
        "expected_pn": "5009855-5",
        "expected_qty": 2,
        "expected_condition": "OVERHAULED",
        "expected_sn": "SN-BRK-5541",
        "tracking_no": "US-FAA-7818-10",
        "org_name": "Landing Gear & Brake Overhaulers",
        "org_address": "900 Runway Blvd, Charlotte, NC 28208",
        "work_order_po": "PO-2026-1010 / WO-8812",
        "item": "1",
        "description": "CARBON BRAKE ASSEMBLY",
        "cert_pn": "5009855-5",
        "cert_qty": 2,
        "cert_sn": "SN-BRK-5541",
        "cert_status": "OVERHAULED",
        "remarks": "Overhauled with new carbon heat stack per CMM 32-40-18.",
        "cert_type": "14",
        "auth_name": "L. Brooks",
        "auth_no": "FAA-CRS-LG2R88",
        "auth_date": "19-MAR-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Freno reacondicionado conforme a orden de compra."
    },
    {
        "case_id": "CERT-11",
        "file_name": "cert_11_err_condition_mismatch.pdf",
        "po_number": "PO-2026-1011",
        "expected_pn": "35-224-3",
        "expected_qty": 1,
        "expected_condition": "NEW",
        "expected_sn": "SN-HYD-9932",
        "tracking_no": "US-FAA-7818-11",
        "org_name": "HydroPower Aero Systems Inc.",
        "org_address": "66 Hydraulic Rd, Cleveland, OH 44135",
        "work_order_po": "PO-2026-1011",
        "item": "1",
        "description": "HYDRAULIC ENGINE DRIVEN PUMP",
        "cert_pn": "35-224-3",
        "cert_qty": 1,
        "cert_sn": "SN-HYD-9932",
        # ERROR: Condición OVERHAULED cuando la PO requería NEW
        "cert_status": "OVERHAULED",
        "remarks": "Overhauled per CMM 29-10-02. Pressure flow tested.",
        "cert_type": "14",
        "auth_name": "S. Novak",
        "auth_no": "FAA-CRS-HP1R77",
        "auth_date": "14-FEB-2026",
        "is_ok": False,
        "error_type": "CONDITION_MISMATCH",
        "explanation": "Rechazar: Condición incorrecta. La PO especificaba pieza 'NEW' pero el certificado indica 'OVERHAULED'."
    },
    {
        "case_id": "CERT-12",
        "file_name": "cert_12_ok_encoder.pdf",
        "po_number": "PO-2026-1012",
        "expected_pn": "45-0428-1",
        "expected_qty": 1,
        "expected_condition": "NEW",
        "expected_sn": "SN-ENC-302",
        "tracking_no": "US-FAA-7818-12",
        "org_name": "Avionics Sensor Technologies",
        "org_address": "220 Altitude Way, Denver, CO 80249",
        "work_order_po": "PO-2026-1012",
        "item": "1",
        "description": "CABIN ALTITUDE ENCODER",
        "cert_pn": "45-0428-1",
        "cert_qty": 1,
        "cert_sn": "SN-ENC-302",
        "cert_status": "NEW",
        "remarks": "Calibrated per TSO-C88a. Static pressure test passed.",
        "cert_type": "13",
        "auth_name": "B. Henderson",
        "auth_no": "DMIR-441920",
        "auth_date": "28-JAN-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Sensor calibrado con trazabilidad y condición nueva."
    },
    {
        "case_id": "CERT-13",
        "file_name": "cert_13_ok_exciter.pdf",
        "po_number": "PO-2026-1013",
        "expected_pn": "10-60600-1",
        "expected_qty": 4,
        "expected_condition": "NEW",
        "expected_sn": "BATCH-IGN-88",
        "tracking_no": "US-FAA-7818-13",
        "org_name": "Turbine Ignition Systems LLC",
        "org_address": "180 Spark Rd, Indianapolis, IN 46241",
        "work_order_po": "PO-2026-1013",
        "item": "1",
        "description": "IGNITION EXCITER UNIT",
        "cert_pn": "10-60600-1",
        "cert_qty": 4,
        "cert_sn": "BATCH-IGN-88",
        "cert_status": "NEW",
        "remarks": "High-energy spark ignition units. Qualified under MIL-PRF-85352.",
        "cert_type": "13",
        "auth_name": "E. Vance",
        "auth_no": "DMIR-612033",
        "auth_date": "08-APR-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Lote de ignición certificado sin discrepancias."
    },
    {
        "case_id": "CERT-14",
        "file_name": "cert_14_err_shelf_life_expired.pdf",
        "po_number": "PO-2026-1014",
        "expected_pn": "PR-1422-B2",
        "expected_qty": 6,
        "expected_condition": "NEW",
        "expected_sn": "LOT-SL-2021",
        "tracking_no": "US-FAA-7818-14",
        "org_name": "Polymer Aerospace Sealants Corp",
        "org_address": "330 Chemistry Way, Glendale, CA 91201",
        "work_order_po": "PO-2026-1014",
        "item": "1",
        "description": "AIRCRAFT FUEL TANK SEALANT",
        "cert_pn": "PR-1422-B2",
        "cert_qty": 6,
        "cert_sn": "LOT-SL-2021",
        "cert_status": "NEW",
        # ERROR: Shelf Life Vencido (Cure 2020, venció en 2022)
        "remarks": "CURE DATE: 2Q2020. SHELF LIFE: 24 MONTHS. EXPIRY DATE: 30-JUN-2022. Store between 50F and 75F.",
        "cert_type": "13",
        "auth_name": "H. Schultz",
        "auth_no": "DMIR-901145",
        "auth_date": "10-JUL-2020",
        "is_ok": False,
        "error_type": "SHELF_LIFE_EXPIRED",
        "explanation": "Rechazar: Material caducado (Shelf Life Vencido). Expiró el 30-JUN-2022 según Bloque 12."
    },
    {
        "case_id": "CERT-15",
        "file_name": "cert_15_ok_elt.pdf",
        "po_number": "PO-2026-1015",
        "expected_pn": "2600-1A",
        "expected_qty": 1,
        "expected_condition": "INSPECTED/TESTED",
        "expected_sn": "SN-ELT-6011",
        "tracking_no": "US-FAA-7818-15",
        "org_name": "Emergency Avionics Certifications Ltd",
        "org_address": "88 Beacon Dr, Houston, TX 77032",
        "work_order_po": "PO-2026-1015 / WO-5112",
        "item": "1",
        "description": "EMERGENCY LOCATOR TRANSMITTER (ELT)",
        "cert_pn": "2600-1A",
        "cert_qty": 1,
        "cert_sn": "SN-ELT-6011",
        "cert_status": "INSPECTED/TESTED",
        "remarks": "406 MHz signal radiated test passed per RTCA DO-204A. Battery expiry: 2030.",
        "cert_type": "14",
        "auth_name": "C. Ortiz",
        "auth_no": "FAA-CRS-EA3R55",
        "auth_date": "14-FEB-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. ELT probado e inspeccionado conforme a pedido."
    },
    {
        "case_id": "CERT-16",
        "file_name": "cert_16_err_missing_signature.pdf",
        "po_number": "PO-2026-1016",
        "expected_pn": "3110-0012",
        "expected_qty": 1,
        "expected_condition": "NEW",
        "expected_sn": "SN-FCL-404",
        "tracking_no": "US-FAA-7818-16",
        "org_name": "Precision Flight Controls LLC",
        "org_address": "150 Lever Way, Seattle, WA 98124",
        "work_order_po": "PO-2026-1016",
        "item": "1",
        "description": "FLAP CONTROL LEVER DETENT",
        "cert_pn": "3110-0012",
        "cert_qty": 1,
        "cert_sn": "SN-FCL-404",
        "cert_status": "NEW",
        "remarks": "Manufactured to approved drawings.",
        # ERROR: Sin firma ni autorización en Bloque 13
        "cert_type": "13",
        "auth_name": "",       # VACÍO
        "auth_no": "",         # VACÍO
        "auth_date": "",       # VACÍO
        "is_ok": False,
        "error_type": "MISSING_SIGNATURE",
        "explanation": "Rechazar: Documento inválido / Trazabilidad rota. Bloque 13 sin firma autorizada ni fecha de emisión."
    },
    {
        "case_id": "CERT-17",
        "file_name": "cert_17_ok_radar.pdf",
        "po_number": "PO-2026-1017",
        "expected_pn": "732-108-01",
        "expected_qty": 1,
        "expected_condition": "OVERHAULED",
        "expected_sn": "SN-RDR-8100",
        "tracking_no": "US-FAA-7818-17",
        "org_name": "Radar & Radio Systems MRO",
        "org_address": "700 Microwave Blvd, Melbourne, FL 32901",
        "work_order_po": "PO-2026-1017 / WO-7011",
        "item": "1",
        "description": "WEATHER RADAR TRANSCEIVER",
        "cert_pn": "732-108-01",
        "cert_qty": 1,
        "cert_sn": "SN-RDR-8100",
        "cert_status": "OVERHAULED",
        "remarks": "Magnetron replaced. RF power output calibrated per CMM 34-41-15.",
        "cert_type": "14",
        "auth_name": "F. Gutierrez",
        "auth_no": "FAA-CRS-RR8R02",
        "auth_date": "25-MAR-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Radar certificado y serial coincidente."
    },
    {
        "case_id": "CERT-18",
        "file_name": "cert_18_err_pn_digit_swap.pdf",
        "po_number": "PO-2026-1018",
        "expected_pn": "740-0158-001",
        "expected_qty": 1,
        "expected_condition": "REPAIRED",
        "expected_sn": "SN-ADC-1224",
        "tracking_no": "US-FAA-7818-18",
        "org_name": "AirData Instruments Lab",
        "org_address": "520 Pitot Dr, Tulsa, OK 74115",
        "work_order_po": "PO-2026-1018",
        "item": "1",
        "description": "AIR DATA COMPUTER (ADC)",
        # ERROR: Dígitos 58 cambiados a 85 en el PN
        "cert_pn": "740-0185-001",
        "cert_qty": 1,
        "cert_sn": "SN-ADC-1224",
        "cert_status": "REPAIRED",
        "remarks": "Pitot-static transducer recalibrated. Tested per CMM 34-12-09.",
        "cert_type": "14",
        "auth_name": "M. Fletcher",
        "auth_no": "FAA-CRS-AD6R31",
        "auth_date": "04-MAY-2026",
        "is_ok": False,
        "error_type": "PN_DIVERGENCE",
        "explanation": "Rechazar: PN con dígitos invertidos. Se esperaba 740-0158-001 y el certificado dice 740-0185-001."
    },
    {
        "case_id": "CERT-19",
        "file_name": "cert_19_ok_valve.pdf",
        "po_number": "PO-2026-1019",
        "expected_pn": "9008-01",
        "expected_qty": 3,
        "expected_condition": "NEW",
        "expected_sn": "N/A",
        "tracking_no": "US-FAA-7818-19",
        "org_name": "Cabin Systems Components Corp",
        "org_address": "410 Galley Way, San Antonio, TX 78216",
        "work_order_po": "PO-2026-1019",
        "item": "1",
        "description": "GALLEY COFFEE MAKER WATER VALVE",
        "cert_pn": "9008-01",
        "cert_qty": 3,
        "cert_sn": "N/A",
        "cert_status": "NEW",
        "remarks": "Hydrostatic pressure test: 150 PSI satisfactory. Direct replacement.",
        "cert_type": "13",
        "auth_name": "P. Soto",
        "auth_no": "DMIR-224190",
        "auth_date": "17-FEB-2026",
        "is_ok": True,
        "error_type": "NONE",
        "explanation": "Conforme. Válvulas nuevas con cantidad y especificación coincidente."
    },
    {
        "case_id": "CERT-20",
        "file_name": "cert_20_err_multiple_critical.pdf",
        "po_number": "PO-2026-1020",
        "expected_pn": "D50000-10",
        "expected_qty": 10,
        "expected_condition": "NEW",
        "expected_sn": "BATCH-LAT-90",
        "tracking_no": "US-FAA-7818-20",
        "org_name": "AeroLatch Hardware Engineering",
        "org_address": "812 Fastener Rd, Phoenix, AZ 85040",
        "work_order_po": "PO-2026-1020",
        "item": "1",
        "description": "PASSENGER SERVICE UNIT LATCH",
        # ERROR 1: PN con sufijo MOD no pedido
        "cert_pn": "D50000-10-MOD",
        # ERROR 2: Cantidad 5 en vez de 10
        "cert_qty": 5,
        "cert_sn": "BATCH-LAT-90",
        "cert_status": "NEW",
        "remarks": "Modified latch mechanism per Service Letter SL-2025-01.",
        "cert_type": "13",
        "auth_name": "G. Lawson",
        "auth_no": "DMIR-771209",
        "auth_date": "11-MAR-2026",
        "is_ok": False,
        "error_type": "MULTIPLE_ERRORS",
        "explanation": "Rechazar: Múltiples discrepancias críticas. PN no solicitado (D50000-10-MOD) y cantidad incompleta (5 de 10)."
    }
]


def draw_8130_pdf(case: dict, target_path: Path):
    """
    Dibuja un certificado en formato PDF que imita fielmente la grilla del FAA Form 8130-3 (Rev. 02-14).
    Orientación: Horizontal (Landscape Letter: 792 x 612 pt).
    """
    c = canvas.Canvas(str(target_path), pagesize=landscape(letter))
    width, height = landscape(letter)

    # Configuración de márgenes
    left_m = 25
    right_m = width - 25
    top_m = height - 25
    bottom_m = 25

    # Marco exterior
    c.setLineWidth(1.2)
    c.setStrokeColor(colors.black)
    c.rect(left_m, bottom_m, right_m - left_m, top_m - bottom_m)

    # -------------------------------------------------------------
    # FILA 1: Encabezado (Bloque 1, Título Principal, Bloque 3)
    # y: 515 a 587
    # -------------------------------------------------------------
    c.line(left_m, 515, right_m, 515)
    
    # Bloque 1: Autoridad Aeronáutica
    c.line(190, 515, 190, top_m)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 5, top_m - 12, "1. Approving Civil Aviation Authority/Country:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(left_m + 15, top_m - 32, "FAA / UNITED STATES")

    # Título Central
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString((190 + 580) / 2, top_m - 20, "AUTHORIZED RELEASE CERTIFICATE")
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString((190 + 580) / 2, top_m - 35, "FAA Form 8130-3, AIRWORTHINESS APPROVAL TAG")

    # Bloque 3: Form Tracking Number
    c.line(580, 515, 580, top_m)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(585, top_m - 12, "3. Form Tracking Number:")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(590, top_m - 32, case["tracking_no"])

    # -------------------------------------------------------------
    # FILA 2: Bloque 4 (Organización) y Bloque 5 (Work Order / Contract / PO)
    # y: 450 a 515
    # -------------------------------------------------------------
    c.line(left_m, 450, right_m, 450)
    c.line(580, 450, 580, 515)

    # Bloque 4
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 5, 505, "4. Organization Name and Address:")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(left_m + 15, 490, case["org_name"])
    c.setFont("Helvetica", 8)
    c.drawString(left_m + 15, 475, case["org_address"])

    # Bloque 5
    c.setFont("Helvetica-Bold", 7)
    c.drawString(585, 505, "5. Work Order/Contract/Invoice Number:")
    c.setFont("Helvetica-Bold", 9)
    c.drawString(590, 480, case["work_order_po"])

    # -------------------------------------------------------------
    # FILA 3: Datos de la Parte (Bloques 6 al 11)
    # y: 380 a 450
    # -------------------------------------------------------------
    c.line(left_m, 420, right_m, 420)  # Separador entre títulos y valores
    c.line(left_m, 375, right_m, 375)  # Fondo de la fila de partes

    # Columnas:
    # 6. Item: 25 - 65
    # 7. Description: 65 - 260
    # 8. Part Number: 260 - 430
    # 9. Quantity: 430 - 495
    # 10. Serial Number: 495 - 640
    # 11. Status/Work: 640 - 767
    col_x = [65, 260, 430, 495, 640]
    for x in col_x:
        c.line(x, 375, x, 450)

    # Encabezados
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 4, 435, "6. Item:")
    c.drawString(70, 435, "7. Description:")
    c.drawString(265, 435, "8. Part Number:")
    c.drawString(435, 435, "9. Quantity:")
    c.drawString(500, 435, "10. Serial Number:")
    c.drawString(645, 435, "11. Status/Work:")

    # Valores
    c.setFont("Helvetica-Bold", 9)
    c.drawCentredString((left_m + 65) / 2, 395, case["item"])
    c.drawString(70, 395, case["description"])
    c.drawString(265, 395, case["cert_pn"])
    c.drawCentredString((430 + 495) / 2, 395, str(case["cert_qty"]))
    c.drawString(500, 395, case["cert_sn"])
    c.drawString(645, 395, case["cert_status"])

    # -------------------------------------------------------------
    # FILA 4: Bloque 12 (Remarks / Observaciones / Shelf Life)
    # y: 275 a 375
    # -------------------------------------------------------------
    c.line(left_m, 275, right_m, 275)
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 5, 365, "12. Remarks:")
    c.setFont("Helvetica", 8)
    
    # Manejo de texto de observaciones
    remarks_text = case["remarks"]
    c.drawString(left_m + 15, 345, remarks_text)

    # -------------------------------------------------------------
    # FILA 5: Bloques de Certificación (Bloque 13 izq / Bloque 14 der)
    # y: 85 a 275
    # -------------------------------------------------------------
    c.line(left_m, 85, right_m, 85)
    mid_x = (left_m + right_m) / 2  # 396 pt
    c.line(mid_x, 85, mid_x, 275)

    # Líneas horizontales internas para firmas (Bloques 13 y 14)
    c.line(left_m, 245, right_m, 245)
    c.line(left_m, 175, right_m, 175)
    c.line(left_m, 125, right_m, 125)

    # Sub-columnas internas para 13b / 13c y 14b / 14c
    c.line(left_m + 220, 125, left_m + 220, 175)
    c.line(mid_x + 220, 125, mid_x + 220, 175)

    # ---- BLOQUE 13: Certificación de Fabricación / Nueva ----
    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 5, 263, "13a. Certifies items identified above were manufactured in conformity to:")
    c.setFont("Helvetica", 7)
    c.drawString(left_m + 15, 252, "[X] Approved design data and are in a condition for safe operation.")

    c.setFont("Helvetica-Bold", 7)
    c.drawString(left_m + 5, 165, "13b. Authorized Signature:")
    c.drawString(left_m + 225, 165, "13c. Approval/Auth No:")

    c.drawString(left_m + 5, 115, "13d. Name (Typed or Printed):")
    c.drawString(left_m + 225, 115, "13e. Date (dd/mmm/yyyy):")

    if case["cert_type"] == "13":
        if case["auth_name"]:
            # Firma simulada
            c.setFont("Times-Italic", 12)
            c.drawString(left_m + 20, 140, f"/s/ {case['auth_name']}")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(left_m + 230, 140, case["auth_no"])
            c.drawString(left_m + 20, 95, case["auth_name"])
            c.drawString(left_m + 230, 95, case["auth_date"])
        else:
            # Caso con firma vacía intencional
            c.setFont("Helvetica-Oblique", 8)
            c.drawString(left_m + 20, 140, "[NO SIGNATURE]")

    # ---- BLOQUE 14: Certificación de Mantenimiento / Retorno a Servicio ----
    c.setFont("Helvetica-Bold", 7)
    c.drawString(mid_x + 5, 263, "14a. [X] 14 CFR 43.9 Return to Service")
    c.setFont("Helvetica", 6.5)
    c.drawString(mid_x + 5, 252, "Certifies work in Block 11 was accomplished in accordance with Title 14 CFR, part 43.")

    c.setFont("Helvetica-Bold", 7)
    c.drawString(mid_x + 5, 165, "14b. Authorized Signature:")
    c.drawString(mid_x + 225, 165, "14c. Approval/Cert No:")

    c.drawString(mid_x + 5, 115, "14d. Name (Typed or Printed):")
    c.drawString(mid_x + 225, 115, "14e. Date (dd/mmm/yyyy):")

    if case["cert_type"] == "14":
        if case["auth_name"]:
            c.setFont("Times-Italic", 12)
            c.drawString(mid_x + 20, 140, f"/s/ {case['auth_name']}")
            c.setFont("Helvetica-Bold", 8)
            c.drawString(mid_x + 230, 140, case["auth_no"])
            c.drawString(mid_x + 20, 95, case["auth_name"])
            c.drawString(mid_x + 230, 95, case["auth_date"])

    # -------------------------------------------------------------
    # PIE DE PÁGINA (Footer)
    # y: 25 a 85
    # -------------------------------------------------------------
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(width / 2, 72, "User/Installer Responsibilities")
    c.setFont("Helvetica", 5.5)
    c.drawString(left_m + 10, 60, "It is important to understand that the existence of this document alone does not automatically constitute authority to install the aircraft engine/propeller/article.")
    c.drawString(left_m + 10, 50, "Statements in Blocks 13a and 14a do not constitute installation certification. In all cases, aircraft maintenance records must contain an installation certification.")

    c.setFont("Helvetica-Bold", 8)
    c.drawString(left_m + 5, 32, "FAA Form 8130-3 (02-14)")
    c.drawString(right_m - 120, 32, "NSN: 0052-00-012-9005")

    c.save()


def generate_all():
    """Genera todos los PDFs, el CSV de POs y el JSON de Ground Truth."""
    print("Iniciando generación de datos sintéticos...")

    # 1. Generar los 20 PDFs
    for case in CASES:
        pdf_path = CERTS_DIR / case["file_name"]
        draw_8130_pdf(case, pdf_path)
        print(f" -> Creado PDF: {case['file_name']} ({'OK' if case['is_ok'] else 'ERROR: ' + case['error_type']})")

    # 2. Generar el archivo CSV de Órdenes de Compra
    csv_path = ORDERS_DIR / "purchase_orders.csv"
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "po_number",
            "expected_pn",
            "expected_qty",
            "expected_condition",
            "expected_sn",
            "description",
            "matching_cert_file"
        ])
        for case in CASES:
            writer.writerow([
                case["po_number"],
                case["expected_pn"],
                case["expected_qty"],
                case["expected_condition"],
                case["expected_sn"],
                case["description"],
                case["file_name"]
            ])
    print(f" -> Creado CSV de Órdenes de Compra: {csv_path}")

    # 3. Generar el JSON de Ground Truth
    gt_path = DATA_DIR / "ground_truth.json"
    with open(gt_path, mode="w", encoding="utf-8") as f:
        json.dump(CASES, f, indent=2, ensure_ascii=False)
    print(f" -> Creado JSON de Ground Truth: {gt_path}")
    print("\n¡Dataset sintético generado exitosamente!")


if __name__ == "__main__":
    generate_all()
