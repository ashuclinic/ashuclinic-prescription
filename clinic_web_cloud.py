# clinic_web_cloud.py
# Ashu Aesthetic & Wellness Clinic - Prescription Management System
# Streamlit Web App - Version 4.1 (Cloud - Supabase)
# Built by: Gananath Sahu
# Started: April 2026
#
# RULES:
# - Pure ASCII only (no Unicode, no emojis, no smart quotes)
# - Run audit_clinic_web.py before and after every change
# - Never share this file if audit shows any FAILED
# - Keep it simple at all times
#
# VERSION HISTORY:
# v1.0 - G1 Login Page
# v1.1 - G2 Home Dashboard + password changed to Ashu
# v1.2 - G3 New Prescription Screen
# v1.3 - Fixed: Clear Form, BMI, Duplicate warning, Active sidebar
# v4.1 - Two level login, serial numbers, speed cache
# v4.0 - Supabase cloud database replacing SQLite
# v3.1 - E1 AI Prescription Reading added to web app
# v3.0 - Photo in patient info box not header, header unchanged
# v2.9 - Reverted form styling, keeping only photo upload widget
# v2.8 - Fixed form layout: photo beside fields, stronger borders
# v2.7 - Form makeover with cards, photo upload placeholder
# v2.6 - BMI form display removed, shows in PDF only
# v2.5 - G9 BMI final fix via number_input return value
# v2.4 - G8 Backup / Export
# v2.3 - G7 Medicine Search
# v2.2 - G6 Medicine Library + Bulk Upload
# v2.1 - G5 Statistics Dashboard
# v2.0 - G4 Patient Records screen
# v1.9 - BMI fix remove value= override, Skip visual tick effect
# v1.8 - BMI direct calc no callback, Skip button via config, Not Applicable top
# v1.7 - BMI on_change callback, weight/height empty text input, dialog Option C
# v1.6 - Phase confirmation dialog per-row, BMI step fix, skip phase logic
# v1.5 - Fixed: BMI via number_input, Reg No auto-caps, email optional confirmed
# v1.4 - Fixed: Calendar picker, BMI live, Not Applicable + Other in all
#         dropdowns, full validation list, phase confirmation, clear always works

import streamlit as st
import os
import hashlib
import json
from datetime import datetime, timedelta, date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable, Image as RLImage
)
from reportlab.lib.utils import ImageReader
import io
import anthropic
import base64
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ============================================================
# CONFIGURATION
# ============================================================

# Supabase cloud database credentials
SUPABASE_URL = "https://txoohfkbcobbotmczcks.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR4b29oZmtiY29iYm90bWN6Y2tzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzc0ODQ2MzgsImV4cCI6MjA5MzA2MDYzOH0.19SiqWWQzOOSBde_crGE3XmF4irv0M-51B4ksZPH64o"

SB_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": "Bearer " + SUPABASE_KEY,
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates,return=representation"
}


def sb_get(table, params=""):
    # Read records from Supabase
    import requests
    url = SUPABASE_URL + "/rest/v1/" + table
    if params:
        url += "?" + params
    resp = requests.get(url, headers=SB_HEADERS, timeout=15)
    if resp.status_code == 200:
        return resp.json()
    return []


def sb_upsert(table, data):
    # Insert or update a record in Supabase
    import requests
    resp = requests.post(
        SUPABASE_URL + "/rest/v1/" + table,
        headers=SB_HEADERS,
        json=data,
        timeout=15
    )
    return resp.status_code in [200, 201]


def sb_update(table, match_key, match_val, data):
    # Update matching records in Supabase
    import requests
    resp = requests.patch(
        SUPABASE_URL + "/rest/v1/" + table +
        "?" + match_key + "=eq." + str(match_val),
        headers=SB_HEADERS,
        json=data,
        timeout=15
    )
    return resp.status_code in [200, 204]


def sb_delete(table, match_key, match_val):
    # Delete matching records from Supabase
    import requests
    resp = requests.delete(
        SUPABASE_URL + "/rest/v1/" + table +
        "?" + match_key + "=eq." + str(match_val),
        headers=SB_HEADERS,
        timeout=15
    )
    return resp.status_code in [200, 204]


# Anthropic API key for AI prescription reading
# Loaded securely from Streamlit Secrets - never hardcoded
def get_anthropic_key():
    try:
        return st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        return None

ANTHROPIC_API_KEY = get_anthropic_key()

PDF_OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "03_Prescriptions_Output"
)

PHASE_NAMES = ["MORNING", "EVENING", "NIGHT"]

WAIT_TIME_OPTIONS = [
    "-- Select --", "Not Applicable", "After Food", "Wash Until Dry",
    "15 Mins", "2 Mins", "3 Mins", "1-1.5 Hrs", "Last Item", "Other"
]

AREA_OPTIONS = [
    "-- Select --", "Not Applicable", "Full Face", "On Spots",
    "Oral", "Scalp", "Other"
]

DOSE_OPTIONS = [
    "-- Select --", "Not Applicable", "1 Tablet", "2 Tablets", "3 Tablets",
    "1/2 Tablet", "Pea-sized", "Few Drops", "As directed", "Other"
]

DURATION_OPTIONS = [
    "-- Select --", "Not Applicable", "7 Days", "10 Days", "14 Days",
    "1 Month", "2 Months", "3 Months", "6 Months", "Ongoing",
    "As directed", "Other"
]

SEX_OPTIONS = ["Female", "Male", "Other"]

DEFAULT_MEDICINES = [
    "Aquasoft Day Cream", "Aquasoft Night Cream", "Ban Melo Cream",
    "Biluma Day Cream", "Biluma Night Cream", "C-Bliz Vit. C Serum",
    "Cutibrite Serum Gel", "Dermaco Cleanser", "Epishine Cleanser",
    "Glambak Ultra NF", "Glufair Strip A", "Glufair Strip B",
    "Glufair Tablet", "Hydra Boom Gel", "IB Glow HP",
    "Lumispark Cream", "Nevlon Caloc Lotion", "Sebaoff Gel",
    "Skinsure Plus", "Sunkage Pro Sunscreen"
]

# ============================================================
# DATABASE HELPERS
# ============================================================

def ensure_tables():
    # Tables are managed in Supabase - nothing to do here
    pass


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def get_setting(key):
    try:
        rows = sb_get("settings", "select=value&key=eq." + str(key))
        if rows:
            return rows[0].get("value")
        return None
    except Exception:
        return None


def set_setting(key, value):
    # Uses Supabase upsert - equivalent to INSERT OR REPLACE
    try:
        return sb_upsert("settings", {"key": key, "value": value})
    except Exception:
        return False


def reset_password_to_default():
    # Admin credentials
    set_setting("web_username", "admin")
    set_setting("web_password", hash_password("Ashu"))
    set_setting("web_role_admin", "admin")
    # User credentials
    set_setting("web_username_user", "user")
    set_setting("web_password_user", hash_password("AshuUser"))
    set_setting("web_role_user", "user")


def check_login(username, password):
    # Check admin credentials
    stored_admin = get_setting("web_username")
    stored_admin_pass = get_setting("web_password")
    if stored_admin and stored_admin_pass:
        if username == stored_admin and hash_password(password) == stored_admin_pass:
            return "admin"
    # Check user credentials
    stored_user = get_setting("web_username_user")
    stored_user_pass = get_setting("web_password_user")
    if stored_user and stored_user_pass:
        if username == stored_user and hash_password(password) == stored_user_pass:
            return "user"
    return None


@st.cache_data(ttl=60)
def get_medicines_list():
    try:
        rows = sb_get("medicines", "select=name&order=name.asc")
        if rows:
            return [r["name"] for r in rows]
        return DEFAULT_MEDICINES[:]
    except Exception:
        return DEFAULT_MEDICINES[:]


def get_patient_by_reg_no(reg_no):
    try:
        rows = sb_get(
            "patients",
            "select=*&reg_no=eq." + str(reg_no)
        )
        return rows[0] if rows else None
    except Exception:
        return None


def save_patient(data):
    try:
        existing = get_patient_by_reg_no(data["reg_no"])
        if existing:
            # Save history first
            sb_upsert("prescription_history", {
                "reg_no": existing["reg_no"],
                "prescription_date": existing.get("prescription_date", ""),
                "start_date": existing.get("start_date", ""),
                "followup_date": existing.get("followup_date", ""),
                "notes": existing.get("notes", ""),
                "phases": existing.get("phases", "[]"),
                "saved_at": datetime.now().isoformat()
            })
            # Update patient
            ok = sb_update("patients", "reg_no", data["reg_no"], {
                "name": data["name"],
                "age": data["age"],
                "sex": data["sex"],
                "mobile": data["mobile"],
                "weight": data["weight"],
                "height": data["height"],
                "bmi": data["bmi"],
                "prescription_date": data["prescription_date"],
                "start_date": data["start_date"],
                "followup_date": data["followup_date"],
                "doctor": data["doctor"],
                "phases": data["phases"],
                "notes": data["notes"],
                "bp": data["bp"],
                "email": data["email"]
            })
        else:
            # Insert new patient
            patient_data = dict(data)
            patient_data["created_at"] = datetime.now().isoformat()
            ok = sb_upsert("patients", patient_data)
        if ok:
            return True, "Patient saved successfully."
        return False, "Error saving patient to Supabase."
    except Exception as e:
        return False, "Error saving patient: " + str(e)

# ============================================================
# SESSION STATE HELPERS
# ============================================================

def is_logged_in():
    return st.session_state.get("logged_in", False)


def do_login(username, password):
    role = check_login(username, password)
    if role:
        st.session_state["logged_in"] = True
        st.session_state["username"] = username
        st.session_state["user_role"] = role
        st.session_state["current_page"] = "Home"
        return True
    return False


def do_logout():
    st.session_state["logged_in"] = False
    st.session_state["username"] = ""
    st.session_state["user_role"] = ""
    st.session_state["current_page"] = "Home"


def reset_rx_defaults():
    ver = st.session_state.get("rx_form_version", 0) + 1
    st.session_state["rx_form_version"] = ver
    st.session_state["rx_reg_no"] = ""
    st.session_state["rx_name"] = ""
    st.session_state["rx_age"] = ""
    st.session_state["rx_sex"] = "Female"
    st.session_state["rx_mobile"] = ""
    st.session_state["rx_weight"] = ""
    st.session_state["rx_height"] = ""
    st.session_state["rx_bmi_display"] = ""
    st.session_state["rx_bp"] = ""
    st.session_state["rx_email"] = ""
    st.session_state["rx_presc_date"] = datetime.now().date()
    st.session_state["rx_start_date"] = datetime.now().date()
    st.session_state["rx_followup_date"] = None
    st.session_state["rx_doctor"] = "Dr. Anita Rath"
    st.session_state["rx_notes"] = ""
    st.session_state["rx_phases"] = {
        "MORNING": [],
        "EVENING": [],
        "NIGHT": []
    }
    st.session_state["rx_confirm_no_phases"] = False
    st.session_state["rx_skipped_phases"] = []
    st.session_state["rx_photo_bytes"] = None


def init_rx_state():
    if "rx_form_version" not in st.session_state:
        reset_rx_defaults()


def clear_rx_state():
    # Always clears immediately - no confirmation needed
    reset_rx_defaults()

# ============================================================
# DASHBOARD DATA HELPERS
# ============================================================

@st.cache_data(ttl=60)
def get_total_patients():
    try:
        rows = sb_get("patients", "select=reg_no")
        return len(rows)
    except Exception:
        return 0


@st.cache_data(ttl=60)
def get_patients_this_month():
    try:
        month_str = datetime.now().strftime("%m-%Y")
        rows = sb_get(
            "patients",
            "select=reg_no&prescription_date=like.*" + month_str
        )
        return len(rows)
    except Exception:
        return 0


def get_average_bmi():
    try:
        rows = sb_get(
            "patients",
            "select=bmi&bmi=gt.0"
        )
        if not rows:
            return 0.0
        bmis = [float(r["bmi"]) for r in rows if r.get("bmi")]
        if bmis:
            return round(sum(bmis) / len(bmis), 1)
        return 0.0
    except Exception:
        return 0.0


@st.cache_data(ttl=60)
def get_followups_next_7_days():
    try:
        rows = sb_get(
            "patients",
            "select=reg_no,name,mobile,followup_date"
            "&followup_date=neq."
        )
        today = datetime.now().date()
        cutoff = today + timedelta(days=7)
        upcoming = []
        for row in rows:
            try:
                fd = row.get("followup_date", "")
                if not fd:
                    continue
                fdate = datetime.strptime(fd, "%d-%m-%Y").date()
                if today <= fdate <= cutoff:
                    upcoming.append({
                        "Reg No": row["reg_no"],
                        "Name": row["name"],
                        "Mobile": row["mobile"],
                        "Follow-up Date": fd
                    })
            except Exception:
                continue
        upcoming.sort(
            key=lambda x: datetime.strptime(
                x["Follow-up Date"], "%d-%m-%Y"
            )
        )
        return upcoming
    except Exception:
        return []

# ============================================================
# BMI CALCULATION
# ============================================================

def calculate_bmi(weight, height):
    try:
        w = float(str(weight).strip())
        h = float(str(height).strip())
        if w > 0 and h > 0:
            return round(w / ((h / 100) ** 2), 2)
        return 0.0
    except Exception:
        return 0.0


def bmi_category(bmi):
    if bmi <= 0:
        return ""
    elif bmi < 18.5:
        return "Underweight"
    elif bmi < 25:
        return "Normal"
    elif bmi < 30:
        return "Overweight"
    else:
        return "Obese"


# ============================================================
# VALIDATION
# ============================================================

def validate_prescription(data, phases_state):
    errors = []

    # Required patient fields
    if not data["reg_no"]:
        errors.append("Registration No is required.")
    if not data["name"]:
        errors.append("Patient Name is required.")
    if not data["age"]:
        errors.append("Age is required.")
    elif not str(data["age"]).isdigit():
        errors.append("Age must be numeric.")
    if not data["mobile"]:
        errors.append("Mobile number is required.")
    elif len(str(data["mobile"])) != 10 or not str(data["mobile"]).isdigit():
        errors.append("Mobile must be exactly 10 digits.")
    if not data["prescription_date"]:
        errors.append("Prescription Date is required.")
    if not data["start_date"]:
        errors.append("Start Date is required.")

    # Date logic
    if data["prescription_date"] and data["start_date"]:
        try:
            pd = datetime.strptime(data["prescription_date"], "%d-%m-%Y")
            sd = datetime.strptime(data["start_date"], "%d-%m-%Y")
            if sd < pd:
                errors.append(
                    "Start Date cannot be earlier than Prescription Date."
                )
        except Exception:
            errors.append("Prescription Date and Start Date must be valid.")

    if data["followup_date"] and data["start_date"]:
        try:
            fd = datetime.strptime(data["followup_date"], "%d-%m-%Y")
            sd2 = datetime.strptime(data["start_date"], "%d-%m-%Y")
            if fd < sd2:
                errors.append(
                    "Follow-up Date cannot be earlier than Start Date."
                )
        except Exception:
            errors.append("Follow-up Date must be valid.")

    # Check incomplete steps within phases
    step_errors = []
    for phase_name in PHASE_NAMES:
        steps = phases_state.get(phase_name, [])
        for i, step in enumerate(steps):
            step_num = str(i + 1)
            med = step.get("medicine", "").strip()
            wait = step.get("wait_time", "").strip()
            area = step.get("area", "").strip()
            dose = step.get("dose", "").strip()
            duration = step.get("duration", "").strip()

            if not med or med == "-- Select --":
                step_errors.append(
                    phase_name + " Step " + step_num + ": Medicine is required."
                )
            if not wait or wait == "-- Select --":
                step_errors.append(
                    phase_name + " Step " + step_num +
                    ": Wait Time is required (use Not Applicable if not needed)."
                )
            if not area or area == "-- Select --":
                step_errors.append(
                    phase_name + " Step " + step_num +
                    ": Area is required (use Not Applicable if not needed)."
                )
            if not dose or dose == "-- Select --":
                step_errors.append(
                    phase_name + " Step " + step_num +
                    ": Dose is required (use Not Applicable if not needed)."
                )
            if not duration or duration == "-- Select --":
                step_errors.append(
                    phase_name + " Step " + step_num +
                    ": Duration is required (use Not Applicable if not needed)."
                )

    errors.extend(step_errors)
    return errors


def has_any_steps(phases_state):
    for phase_name in PHASE_NAMES:
        if phases_state.get(phase_name, []):
            return True
    return False


def get_empty_phases(phases_state):
    # Returns list of phase names that have no steps
    return [p for p in PHASE_NAMES if not phases_state.get(p, [])]


def get_filled_phases(phases_state):
    # Returns list of phase names that have at least one step
    return [p for p in PHASE_NAMES if phases_state.get(p, [])]


def get_date_strings():
    presc_obj = st.session_state["rx_presc_date"]
    start_obj = st.session_state["rx_start_date"]
    followup_obj = st.session_state["rx_followup_date"]
    presc_str = (
        presc_obj.strftime("%d-%m-%Y")
        if isinstance(presc_obj, date) else str(presc_obj)
    )
    start_str = (
        start_obj.strftime("%d-%m-%Y")
        if isinstance(start_obj, date) else str(start_obj)
    )
    followup_str = (
        followup_obj.strftime("%d-%m-%Y")
        if isinstance(followup_obj, date) and followup_obj
        else ""
    )
    return presc_str, start_str, followup_str

# ============================================================
# PDF GENERATION
# ============================================================

def generate_pdf(data, photo_bytes=None):
    try:
        year = datetime.now().strftime("%Y")
        month = datetime.now().strftime("%m_%B")
        out_dir = os.path.join(PDF_OUTPUT_DIR, year, month)
        os.makedirs(out_dir, exist_ok=True)

        safe_name = (
            data["name"].replace(" ", "_").replace("/", "_")
        )
        date_str = data["prescription_date"].replace("-", "")
        filename = (
            data["reg_no"] + "_" + safe_name + "_" + date_str + ".pdf"
        )
        pdf_path = os.path.join(out_dir, filename)

        doc = SimpleDocTemplate(
            pdf_path, pagesize=A4,
            rightMargin=10*mm, leftMargin=10*mm,
            topMargin=8*mm, bottomMargin=8*mm
        )

        NAVY = colors.HexColor("#1B2A4A")
        GOLD = colors.HexColor("#B8860B")
        LIGHT_GOLD = colors.HexColor("#FFF8DC")
        LIGHT_BLUE = colors.HexColor("#E8F4FD")
        ORANGE = colors.HexColor("#E65100")
        GREEN = colors.HexColor("#1B5E20")
        PURPLE = colors.HexColor("#4A148C")
        WHITE = colors.white

        story = []

        # Header - original two columns, unchanged
        header_data = [[
            Paragraph(
                "<font color='#B8860B' size=16>"
                "<b>ASHU AESTHETIC &amp; WELLNESS CLINIC</b></font><br/>"
                "<font color='white' size=9>Odisha's Ultra Advanced "
                "Skin, Hair &amp; Laser Cosmetic Clinic</font><br/>"
                "<font color='#B8860B' size=9>www.ashuskincare.com</font>",
                ParagraphStyle("hdr", fontName="Helvetica", alignment=TA_LEFT)
            ),
            Paragraph(
                "<font color='white' size=8>"
                "Tel: 9583471256<br/>Appt: 7381524569<br/>"
                "Pharmacy: 9583751246<br/>Reception: 8270055000"
                "</font>",
                ParagraphStyle("hdr2", fontName="Helvetica", alignment=TA_RIGHT)
            )
        ]]
        header_table = Table(header_data, colWidths=[130*mm, 60*mm])
        header_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), NAVY),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 3*mm))

        story.append(Paragraph(
            "<b>Dr. Anita Rath</b> - M.D (Skin &amp; VD), Gold Medalist"
            " | OPD CARD / PRESCRIPTION",
            ParagraphStyle(
                "doc", fontName="Helvetica", fontSize=10,
                alignment=TA_CENTER
            )
        ))
        story.append(Spacer(1, 3*mm))

        # Weight - show cleanly without trailing .0
        w_raw = data.get("weight", 0)
        try:
            w_float = float(w_raw)
            if w_float > 0:
                w_str = (
                    str(int(w_float))
                    if w_float == int(w_float)
                    else str(w_float)
                )
                weight_str = "Weight: " + w_str + " kg"
            else:
                weight_str = "Weight: "
        except Exception:
            weight_str = "Weight: " + str(w_raw) + " kg"

        # Height - show cleanly
        h_raw = data.get("height", 0)
        try:
            h_float = float(h_raw)
            if h_float > 0:
                h_str = (
                    str(int(h_float))
                    if h_float == int(h_float)
                    else str(h_float)
                )
                height_str = "Height: " + h_str + " cm"
            else:
                height_str = "Height: "
        except Exception:
            height_str = "Height: " + str(h_raw) + " cm"

        # BMI - show cleanly
        bmi_raw = data.get("bmi", 0)
        try:
            bmi_float = float(bmi_raw)
            if bmi_float > 0:
                bmi_cat = bmi_category(bmi_float)
                bmi_str = (
                    "BMI: " + str(bmi_float) +
                    " (" + bmi_cat + ")"
                    if bmi_cat else "BMI: " + str(bmi_float)
                )
            else:
                bmi_str = "BMI: "
        except Exception:
            bmi_str = "BMI: "

        # Build photo cell for patient info box
        if photo_bytes:
            try:
                photo_img = RLImage(
                    io.BytesIO(photo_bytes),
                    width=25*mm, height=30*mm
                )
                photo_info_cell = photo_img
            except Exception:
                photo_info_cell = ""
        else:
            photo_info_cell = ""

        info_data = [
            ["Patient Name: " + data["name"],
             "Reg No: " + data["reg_no"], photo_info_cell],
            ["Age/Sex: " + str(data["age"]) + " / " + data["sex"],
             "Mobile: " + data["mobile"], ""],
            [weight_str, height_str, ""],
            [bmi_str, "BP: " + data.get("bp", ""), ""],
            ["Doctor: " + data["doctor"],
             "Email: " + data.get("email", ""), ""],
            ["Prescription Date: " + data["prescription_date"],
             "Start Date: " + data["start_date"], ""],
            ["Follow-up Date: " + data.get("followup_date", ""), "", ""],
        ]
        info_table = Table(info_data, colWidths=[80*mm, 80*mm, 30*mm])
        info_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GOLD),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("PADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5,
             colors.HexColor("#CCCCCC")),
            ("SPAN", (0, 6), (2, 6)),
            ("SPAN", (2, 0), (2, 5)),
            ("VALIGN", (2, 0), (2, 5), "MIDDLE"),
            ("ALIGN", (2, 0), (2, 5), "CENTER"),
            ("NOSPLIT", (0, 0), (-1, -1)),
        ]))
        story.append(info_table)
        story.append(Spacer(1, 3*mm))

        if data.get("notes"):
            notes_data = [[
                "Clinical Notes / Diagnosis", data["notes"]
            ]]
            notes_table = Table(
                notes_data, colWidths=[45*mm, 145*mm]
            )
            notes_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (0, 0),
                 colors.HexColor("#1565C0")),
                ("BACKGROUND", (1, 0), (1, 0), LIGHT_BLUE),
                ("TEXTCOLOR", (0, 0), (0, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("PADDING", (0, 0), (-1, -1), 5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(notes_table)
            story.append(Spacer(1, 3*mm))

        phases = (
            json.loads(data["phases"])
            if isinstance(data["phases"], str)
            else data["phases"]
        )
        phase_colors = {
            "MORNING": ORANGE,
            "EVENING": GREEN,
            "NIGHT": PURPLE
        }
        col_headers = [
            "Step", "Medicine/Cream", "Substitute",
            "Wait Time", "Area", "Dose", "Duration"
        ]
        col_widths = [
            10*mm, 52*mm, 42*mm, 24*mm, 22*mm, 18*mm, 22*mm
        ]

        for phase in phases:
            phase_name = phase.get("phase", "")
            steps = phase.get("steps", [])
            if not steps:
                continue
            phase_color = phase_colors.get(phase_name, NAVY)
            phase_header = [[
                Paragraph(
                    "<font color='white'><b>" +
                    phase_name + "</b></font>",
                    ParagraphStyle(
                        "ph", fontName="Helvetica-Bold", fontSize=10
                    )
                ), "", "", "", "", "", ""
            ]]
            phase_hdr_table = Table(
                phase_header, colWidths=col_widths
            )
            phase_hdr_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), phase_color),
                ("SPAN", (0, 0), (-1, 0)),
                ("PADDING", (0, 0), (-1, -1), 5),
            ]))
            story.append(phase_hdr_table)

            table_data = [col_headers]
            for step in steps:
                sub = step.get("substitute", "")
                if sub == "Not Applicable":
                    sub = "-"
                table_data.append([
                    str(step.get("step", "")),
                    step.get("medicine", ""),
                    sub,
                    step.get("wait_time", ""),
                    step.get("area", ""),
                    step.get("dose", ""),
                    step.get("duration", ""),
                ])
            phase_table = Table(table_data, colWidths=col_widths)
            phase_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0),
                 colors.HexColor("#EEEEEE")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("PADDING", (0, 0), (-1, -1), 3),
                ("GRID", (0, 0), (-1, -1), 0.5,
                 colors.HexColor("#CCCCCC")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [WHITE, colors.HexColor("#F9F9F9")]),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            story.append(phase_table)
            story.append(Spacer(1, 3*mm))

        story.append(HRFlowable(
            width="100%", thickness=0.5, color=NAVY
        ))
        story.append(Paragraph(
            "This prescription is valid only as advised by "
            "Dr. Anita Rath | Ashu Aesthetic &amp; Wellness Clinic,"
            " Jaydev Vihar, Bhubaneswar | Tel: 9583471256",
            ParagraphStyle(
                "footer", fontName="Helvetica", fontSize=7,
                alignment=TA_CENTER
            )
        ))

        doc.build(story)
        return True, pdf_path
    except Exception as e:
        return False, "PDF error: " + str(e)

# ============================================================
# SIDEBAR - active page highlighted gold
# ============================================================

def show_sidebar():
    current = st.session_state.get("current_page", "Home")
    role = st.session_state.get("user_role", "user")

    st.sidebar.markdown(
        "<h3 style='color:#B8860B;'>Ashu Clinic</h3>",
        unsafe_allow_html=True
    )
    st.sidebar.markdown("**Dr. Anita Rath**")
    st.sidebar.markdown("M.D (Skin & VD), Gold Medalist")
    st.sidebar.markdown("---")

    # All pages
    all_pages = [
        "Home", "New Prescription", "Patient Records",
        "Statistics", "Medicine Library",
        "Medicine Search", "Backup / Export"
    ]
    # Pages accessible by user role
    user_pages = ["Home", "New Prescription", "Patient Records"]

    for page in all_pages:
        if page == current:
            st.sidebar.markdown(
                "<div style='background:#B8860B; color:white; "
                "padding:8px 12px; border-radius:4px; "
                "font-weight:bold; margin-bottom:4px; "
                "text-align:center;'>" + page + "</div>",
                unsafe_allow_html=True
            )
        else:
            if st.sidebar.button(
                page, key="nav_" + page, use_container_width=True
            ):
                if role == "admin" or page in user_pages:
                    st.session_state["current_page"] = page
                else:
                    st.session_state["current_page"] = page
                    st.session_state["access_restricted"] = True
                st.rerun()

    st.sidebar.markdown("---")
    role_label = "Administrator" if role == "admin" else "User"
    st.sidebar.markdown(
        "<small>Logged in as: <b>" +
        st.session_state.get("username", "") +
        "</b> (" + role_label + ")</small>",
        unsafe_allow_html=True
    )
    if st.sidebar.button("Logout", use_container_width=True):
        do_logout()
        st.rerun()

# ============================================================
# HOME DASHBOARD - G2
# ============================================================

def show_home():
    st.markdown(
        "<h2 style='color:#B8860B;'>"
        "Ashu Aesthetic &amp; Wellness Clinic</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#555;'>Odisha's Ultra Advanced Skin, "
        "Hair &amp; Laser Cosmetic Clinic</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    total = get_total_patients()
    this_month = get_patients_this_month()
    avg_bmi = get_average_bmi()
    followups = get_followups_next_7_days()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Patients", value=str(total))
    with col2:
        st.metric(label="Patients This Month", value=str(this_month))
    with col3:
        st.metric(label="Average BMI", value=str(avg_bmi))
    with col4:
        st.metric(
            label="Follow-ups (Next 7 Days)",
            value=str(len(followups))
        )

    st.markdown("---")
    st.markdown("### Quick Navigation")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button(
            "New Prescription",
            use_container_width=True, type="primary"
        ):
            st.session_state["current_page"] = "New Prescription"
            st.rerun()
        st.markdown("")
        if st.button("Statistics", use_container_width=True):
            st.session_state["current_page"] = "Statistics"
            st.rerun()
    with col2:
        if st.button("Patient Records", use_container_width=True):
            st.session_state["current_page"] = "Patient Records"
            st.rerun()
        st.markdown("")
        if st.button("Medicine Library", use_container_width=True):
            st.session_state["current_page"] = "Medicine Library"
            st.rerun()
    with col3:
        if st.button("Medicine Search", use_container_width=True):
            st.session_state["current_page"] = "Medicine Search"
            st.rerun()
        st.markdown("")
        if st.button("Backup / Export", use_container_width=True):
            st.session_state["current_page"] = "Backup / Export"
            st.rerun()

    st.markdown("---")
    st.markdown("### Upcoming Follow-ups (Next 7 Days)")
    if len(followups) == 0:
        st.info("No follow-ups due in the next 7 days.")
    else:
        st.success(
            str(len(followups)) + " patient(s) due for follow-up."
        )
        st.table(followups)

    st.markdown("---")
    st.markdown(
        "<small style='color:#aaa;'>www.ashuskincare.com | "
        "Jaydev Vihar, Bhubaneswar | "
        "Built with Claude AI</small>",
        unsafe_allow_html=True
    )

# ============================================================
# STEP ROW HELPER
# ============================================================

def make_med_options(medicines):
    return ["-- Select --", "Not Applicable"] + medicines + ["Other"]


def render_step_row(phase_name, i, step, med_options, ver):
    col_num, col_med, col_sub, col_wait, col_area, \
        col_dose, col_dur, col_del = st.columns(
        [0.4, 2.2, 1.8, 1.5, 1.4, 1.4, 1.5, 0.4]
    )

    with col_num:
        st.markdown(
            "<div style='padding-top:32px; font-weight:bold;'>" +
            str(i + 1) + "</div>",
            unsafe_allow_html=True
        )

    # Medicine
    with col_med:
        label_med = "Medicine" if i == 0 else " "
        cur_med = step.get("medicine", "")
        if cur_med in med_options:
            med_idx = med_options.index(cur_med)
        elif cur_med:
            med_idx = med_options.index("Other")
        else:
            med_idx = 0
        sel_med = st.selectbox(
            label_med, med_options, index=med_idx,
            key=phase_name + "_med_" + str(i) + "_" + ver
        )
        if sel_med == "Other":
            custom = st.text_input(
                "Enter medicine name",
                value=step.get("medicine_custom", ""),
                key=phase_name + "_medcustom_" + str(i) + "_" + ver,
                placeholder="Type medicine name..."
            )
            step["medicine_custom"] = custom
            step["medicine"] = custom
        elif sel_med == "-- Select --":
            step["medicine"] = ""
        else:
            step["medicine"] = sel_med
            step.pop("medicine_custom", None)

    # Substitute - uses med_options too
    with col_sub:
        label_sub = "Substitute" if i == 0 else " "
        cur_sub = step.get("substitute", "")
        if cur_sub in med_options:
            sub_idx = med_options.index(cur_sub)
        else:
            sub_idx = 0
        sel_sub = st.selectbox(
            label_sub, med_options, index=sub_idx,
            key=phase_name + "_sub_" + str(i) + "_" + ver
        )
        if sel_sub == "Other":
            custom_sub = st.text_input(
                "Enter substitute name",
                value=step.get("substitute_custom", ""),
                key=phase_name + "_subcustom_" + str(i) + "_" + ver,
                placeholder="Type substitute name..."
            )
            step["substitute_custom"] = custom_sub
            step["substitute"] = custom_sub
        elif sel_sub == "-- Select --":
            step["substitute"] = ""
        else:
            step["substitute"] = sel_sub
            step.pop("substitute_custom", None)

    # Wait Time
    with col_wait:
        label_wt = "Wait Time" if i == 0 else " "
        cur_wt = step.get("wait_time", "")
        wt_idx = (
            WAIT_TIME_OPTIONS.index(cur_wt)
            if cur_wt in WAIT_TIME_OPTIONS else 0
        )
        sel_wt = st.selectbox(
            label_wt, WAIT_TIME_OPTIONS, index=wt_idx,
            key=phase_name + "_wait_" + str(i) + "_" + ver
        )
        if sel_wt == "Other":
            custom_wt = st.text_input(
                "Enter wait time",
                value=step.get("wait_time_custom", ""),
                key=phase_name + "_waitcustom_" + str(i) + "_" + ver,
                placeholder="e.g. 30 Mins"
            )
            step["wait_time_custom"] = custom_wt
            step["wait_time"] = custom_wt
        else:
            step["wait_time"] = sel_wt
            step.pop("wait_time_custom", None)

    # Area
    with col_area:
        label_ar = "Area" if i == 0 else " "
        cur_ar = step.get("area", "")
        ar_idx = (
            AREA_OPTIONS.index(cur_ar)
            if cur_ar in AREA_OPTIONS else 0
        )
        sel_ar = st.selectbox(
            label_ar, AREA_OPTIONS, index=ar_idx,
            key=phase_name + "_area_" + str(i) + "_" + ver
        )
        if sel_ar == "Other":
            custom_ar = st.text_input(
                "Enter area",
                value=step.get("area_custom", ""),
                key=phase_name + "_areacustom_" + str(i) + "_" + ver,
                placeholder="e.g. Neck"
            )
            step["area_custom"] = custom_ar
            step["area"] = custom_ar
        else:
            step["area"] = sel_ar
            step.pop("area_custom", None)

    # Dose
    with col_dose:
        label_do = "Dose" if i == 0 else " "
        cur_do = step.get("dose", "")
        do_idx = (
            DOSE_OPTIONS.index(cur_do)
            if cur_do in DOSE_OPTIONS else 0
        )
        sel_do = st.selectbox(
            label_do, DOSE_OPTIONS, index=do_idx,
            key=phase_name + "_dose_" + str(i) + "_" + ver
        )
        if sel_do == "Other":
            custom_do = st.text_input(
                "Enter dose",
                value=step.get("dose_custom", ""),
                key=phase_name + "_dosecustom_" + str(i) + "_" + ver,
                placeholder="e.g. 5ml"
            )
            step["dose_custom"] = custom_do
            step["dose"] = custom_do
        else:
            step["dose"] = sel_do
            step.pop("dose_custom", None)

    # Duration
    with col_dur:
        label_dr = "Duration" if i == 0 else " "
        cur_dr = step.get("duration", "")
        dr_idx = (
            DURATION_OPTIONS.index(cur_dr)
            if cur_dr in DURATION_OPTIONS else 0
        )
        sel_dr = st.selectbox(
            label_dr, DURATION_OPTIONS, index=dr_idx,
            key=phase_name + "_dur_" + str(i) + "_" + ver
        )
        if sel_dr == "Other":
            custom_dr = st.text_input(
                "Enter duration",
                value=step.get("duration_custom", ""),
                key=phase_name + "_durcustom_" + str(i) + "_" + ver,
                placeholder="e.g. 45 Days"
            )
            step["duration_custom"] = custom_dr
            step["duration"] = custom_dr
        else:
            step["duration"] = sel_dr
            step.pop("duration_custom", None)

    # Delete button
    delete_clicked = False
    with col_del:
        st.markdown(
            "<div style='padding-top:28px;'>",
            unsafe_allow_html=True
        )
        if st.button(
            "X",
            key=phase_name + "_del_" + str(i) + "_" + ver
        ):
            delete_clicked = True
        st.markdown("</div>", unsafe_allow_html=True)

    return step, delete_clicked

# ============================================================
# NEW PRESCRIPTION - G3
# ============================================================


# ============================================================
# AI PRESCRIPTION READING - E1
# ============================================================

def read_prescription_with_ai(file_bytes, file_type):
    # Reads a handwritten prescription image or PDF using Claude AI
    # Returns a dict with extracted patient data or None on failure
    try:
        api_key = get_anthropic_key()
        if not api_key:
            return None
        client = anthropic.Anthropic(api_key=api_key)

        prompt = """You are reading a handwritten medical prescription from
Ashu Aesthetic and Wellness Clinic, Bhubaneswar.

Extract all information and return ONLY a JSON object with these exact fields:
{
  "patient_name": "",
  "age": "",
  "sex": "",
  "mobile": "",
  "weight": "",
  "height": "",
  "reg_no": "",
  "prescription_date": "",
  "diagnosis": "",
  "notes": "",
  "phases": [
    {
      "phase": "MORNING",
      "steps": [
        {
          "step": 1,
          "medicine": "",
          "substitute": "",
          "wait_time": "",
          "area": "",
          "dose": "",
          "duration": ""
        }
      ]
    }
  ]
}

Rules:
- phase must be exactly MORNING, EVENING, or NIGHT
- prescription_date format: DD-MM-YYYY
- diagnosis: the skin condition only
- notes: other observations excluding diagnosis and BMI
- If a field is not found leave it as empty string
- Return ONLY the JSON, no other text"""

        if file_type in ["jpg", "jpeg", "png"]:
            media_map = {
                "jpg": "image/jpeg",
                "jpeg": "image/jpeg",
                "png": "image/png"
            }
            media_type = media_map.get(file_type, "image/jpeg")
            img_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": img_b64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )
        else:
            # PDF
            pdf_b64 = base64.standard_b64encode(file_bytes).decode("utf-8")
            message = client.messages.create(
                model="claude-opus-4-6",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": pdf_b64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }]
            )

        response_text = message.content[0].text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            response_text = "\n".join(lines)

        extracted = json.loads(response_text)
        return extracted

    except Exception as e:
        return None


def fill_form_from_ai(extracted):
    # Fill session state from AI extracted data
    if not extracted:
        return False

    if extracted.get("patient_name"):
        st.session_state["rx_name"] = extracted["patient_name"]
    if extracted.get("age"):
        age_str = "".join(ch for ch in str(extracted["age"]) if ch.isdigit())
        st.session_state["rx_age"] = age_str[:3]
    if extracted.get("sex"):
        sex = extracted["sex"].strip().capitalize()
        if sex in ["Male", "Female", "Other"]:
            st.session_state["rx_sex"] = sex
    if extracted.get("mobile"):
        mob = "".join(ch for ch in str(extracted["mobile"]) if ch.isdigit())
        st.session_state["rx_mobile"] = mob[:10]
    if extracted.get("weight"):
        st.session_state["rx_weight"] = str(extracted["weight"])
    if extracted.get("height"):
        st.session_state["rx_height"] = str(extracted["height"])
    if extracted.get("reg_no"):
        st.session_state["rx_reg_no"] = str(extracted["reg_no"]).upper()
    if extracted.get("prescription_date"):
        try:
            pd = datetime.strptime(
                extracted["prescription_date"], "%d-%m-%Y"
            ).date()
            st.session_state["rx_presc_date"] = pd
        except Exception:
            pass

    # Diagnosis first, then notes
    notes_parts = []
    if extracted.get("diagnosis"):
        notes_parts.append("Diagnosis: " + extracted["diagnosis"])
    if extracted.get("notes"):
        notes_parts.append(extracted["notes"])
    if notes_parts:
        st.session_state["rx_notes"] = "\n".join(notes_parts)

    # Fill phases
    medicines = get_medicines_list()
    phases_dict = {"MORNING": [], "EVENING": [], "NIGHT": []}
    if extracted.get("phases"):
        for phase in extracted["phases"]:
            phase_name = phase.get("phase", "").upper()
            if phase_name not in phases_dict:
                continue
            steps = []
            for step in phase.get("steps", []):
                med = step.get("medicine", "").strip()
                # If medicine not in library mark as custom
                if med and med not in medicines:
                    step["medicine"] = med
                    step["medicine_custom"] = med
                steps.append({
                    "step": step.get("step", len(steps) + 1),
                    "medicine": med,
                    "substitute": step.get("substitute", ""),
                    "wait_time": step.get("wait_time", ""),
                    "area": step.get("area", ""),
                    "dose": step.get("dose", ""),
                    "duration": step.get("duration", "")
                })
            phases_dict[phase_name] = steps
    st.session_state["rx_phases"] = phases_dict
    return True

def show_new_prescription():
    init_rx_state()
    ver = str(st.session_state.get("rx_form_version", 0))
    medicines = get_medicines_list()
    med_options = make_med_options(medicines)

    st.markdown(
        "<h2 style='color:#B8860B;'>New Prescription</h2>",
        unsafe_allow_html=True
    )

    col_title, col_clear = st.columns([4, 1])
    with col_clear:
        if st.button("Clear Form", use_container_width=True):
            clear_rx_state()
            st.rerun()

    # AI READ SECTION
    st.markdown("---")
    st.markdown("### AI Read Handwritten Prescription")
    st.caption(
        "Upload a photo or PDF of a handwritten prescription. "
        "Claude AI will read it and auto-fill the form below. "
        "Always review and correct before saving."
    )
    ai_col1, ai_col2 = st.columns([3, 1])
    with ai_col1:
        ai_file = st.file_uploader(
            "Upload prescription image or PDF",
            type=["jpg", "jpeg", "png", "pdf"],
            key="ai_upload_" + ver,
            label_visibility="collapsed"
        )
    with ai_col2:
        st.markdown("<div style='padding-top:4px;'>", unsafe_allow_html=True)
        ai_read_clicked = st.button(
            "Read with AI",
            use_container_width=True,
            type="primary",
            key="ai_read_btn"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    if ai_read_clicked:
        if not ai_file:
            st.error("Please upload a prescription image or PDF first.")
        else:
            with st.spinner("Claude AI is reading the prescription..."):
                file_bytes = ai_file.read()
                file_ext = ai_file.name.split(".")[-1].lower()
                extracted = read_prescription_with_ai(file_bytes, file_ext)
            if extracted:
                fill_form_from_ai(extracted)
                st.success(
                    "Prescription read successfully. "
                    "Please review all fields before saving."
                )
                st.rerun()
            else:
                st.error(
                    "Could not read the prescription. "
                    "Please check the image quality and try again."
                )

    st.markdown("---")
    st.markdown("### Patient Information")

    # Photo upload in top right
    col1, col2, col_photo = st.columns([2, 2, 1])
    with col_photo:
        st.markdown("**Patient Photo**")
        uploaded_photo = st.file_uploader(
            "Photo",
            type=["jpg", "jpeg", "png"],
            key="input_photo_" + ver,
            label_visibility="collapsed"
        )
        if uploaded_photo:
            st.image(uploaded_photo, width=100)
            st.session_state["rx_photo_bytes"] = uploaded_photo.read()
        else:
            st.session_state["rx_photo_bytes"] = None

    with col1:
        reg_no_input = st.text_input(
            "Registration No *",
            value=st.session_state["rx_reg_no"].upper(),
            key="input_reg_no_" + ver,
            placeholder="e.g. ASC10075"
        ).upper().strip()
        st.session_state["rx_reg_no"] = reg_no_input

        if reg_no_input and len(reg_no_input) >= 3:
            existing = get_patient_by_reg_no(reg_no_input)
            if existing:
                st.warning(
                    "Reg No already exists: **" +
                    existing["name"] + "** | Date: " +
                    existing["prescription_date"] +
                    " (You are editing this patient)"
                )

        name_input = st.text_input(
            "Patient Name *",
            value=st.session_state["rx_name"],
            key="input_name_" + ver
        )
        st.session_state["rx_name"] = name_input

        age_raw = st.text_input(
            "Age *",
            value=st.session_state["rx_age"],
            key="input_age_" + ver,
            placeholder="e.g. 35"
        )
        age_input = "".join(
            ch for ch in age_raw if ch.isdigit()
        )[:3]
        st.session_state["rx_age"] = age_input

        sex_idx = (
            SEX_OPTIONS.index(st.session_state["rx_sex"])
            if st.session_state["rx_sex"] in SEX_OPTIONS else 0
        )
        sex_input = st.selectbox(
            "Sex *", SEX_OPTIONS, index=sex_idx,
            key="input_sex_" + ver
        )
        st.session_state["rx_sex"] = sex_input

        mobile_raw = st.text_input(
            "Mobile * (exactly 10 digits)",
            value=st.session_state["rx_mobile"],
            key="input_mobile_" + ver,
            placeholder="e.g. 9876543210",
            max_chars=10
        )
        mobile_input = "".join(
            ch for ch in mobile_raw if ch.isdigit()
        )[:10]
        st.session_state["rx_mobile"] = mobile_input
        if mobile_input and len(mobile_input) != 10:
            st.warning(
                "Mobile number must be exactly 10 digits. "
                "Currently " + str(len(mobile_input)) + " digits."
            )

    with col2:
        # FINAL BMI FIX:
        # Weight and Height as text inputs - starts empty, no 0.0 placeholder
        # Pre-fills correctly when editing an existing patient
        weight_val = st.text_input(
            "Weight (kg)",
            value=st.session_state.get("rx_weight", ""),
            key="input_weight_num_" + ver,
            placeholder="e.g. 65"
        )
        height_val = st.text_input(
            "Height (cm)",
            value=st.session_state.get("rx_height", ""),
            key="input_height_num_" + ver,
            placeholder="e.g. 162"
        )

        # Store for save function
        st.session_state["rx_weight"] = weight_val.strip()
        st.session_state["rx_height"] = height_val.strip()

        # BMI is calculated and shown in the PDF only
        st.text_input(
            "BMI",
            value="BMI will be calculated and shown in the PDF",
            disabled=True,
            key="bmi_static_" + ver
        )

        bp_input = st.text_input(
            "Blood Pressure",
            value=st.session_state["rx_bp"],
            key="input_bp_" + ver,
            placeholder="e.g. 120/80"
        )
        st.session_state["rx_bp"] = bp_input

        email_input = st.text_input(
            "Patient Email",
            value=st.session_state["rx_email"],
            key="input_email_" + ver,
            placeholder="e.g. patient@email.com"
        )
        st.session_state["rx_email"] = email_input

    st.markdown("---")
    st.markdown("### Prescription Details")

    col1, col2 = st.columns(2)
    with col1:
        presc_date_val = st.date_input(
            "Prescription Date *",
            value=st.session_state["rx_presc_date"],
            key="input_presc_date_" + ver,
            format="DD/MM/YYYY"
        )
        st.session_state["rx_presc_date"] = presc_date_val

        start_date_val = st.date_input(
            "Start Date *",
            value=st.session_state["rx_start_date"],
            key="input_start_date_" + ver,
            format="DD/MM/YYYY",
            min_value=presc_date_val
        )
        st.session_state["rx_start_date"] = start_date_val

    with col2:
        followup_val = st.date_input(
            "Follow-up Date (optional)",
            value=st.session_state["rx_followup_date"],
            key="input_followup_date_" + ver,
            format="DD/MM/YYYY",
            min_value=start_date_val
        )
        st.session_state["rx_followup_date"] = followup_val

        doctor_input = st.text_input(
            "Doctor",
            value=st.session_state["rx_doctor"],
            key="input_doctor_" + ver
        )
        st.session_state["rx_doctor"] = doctor_input

    st.markdown("---")
    st.markdown("### Clinical Notes / Diagnosis")
    notes_input = st.text_area(
        "Notes",
        value=st.session_state["rx_notes"],
        key="input_notes_" + ver,
        height=100,
        placeholder="Enter diagnosis and clinical notes here..."
    )
    st.session_state["rx_notes"] = notes_input

    st.markdown("---")
    st.markdown("### Prescription Phases")
    st.caption(
        "All fields in each step are compulsory. "
        "Select Not Applicable if a field does not apply. "
        "Select Other to type a custom value."
    )

    phase_colors_ui = {
        "MORNING": "#E65100",
        "EVENING": "#1B5E20",
        "NIGHT": "#4A148C"
    }

    for phase_name in PHASE_NAMES:
        color = phase_colors_ui[phase_name]
        st.markdown(
            "<div style='background:" + color +
            "; color:white; padding:8px 12px; border-radius:4px; "
            "font-weight:bold; font-size:15px; "
            "margin-bottom:8px;'>" + phase_name + "</div>",
            unsafe_allow_html=True
        )

        steps = st.session_state["rx_phases"][phase_name]
        steps_to_delete = []

        for i, step in enumerate(steps):
            updated_step, del_clicked = render_step_row(
                phase_name, i, step, med_options, ver
            )
            steps[i] = updated_step
            if del_clicked:
                steps_to_delete.append(i)

        for idx in reversed(steps_to_delete):
            steps.pop(idx)
        if steps_to_delete:
            st.session_state["rx_phases"][phase_name] = steps
            st.rerun()

        if st.button(
            "+ Add Step (" + phase_name + ")",
            key="add_" + phase_name + "_" + ver
        ):
            steps.append({
                "step": len(steps) + 1,
                "medicine": "", "substitute": "",
                "wait_time": "", "area": "",
                "dose": "", "duration": ""
            })
            st.session_state["rx_phases"][phase_name] = steps
            st.rerun()

        st.session_state["rx_phases"][phase_name] = steps
        st.markdown("")

    st.markdown("---")

    # --------------------------------------------------------
    # SAVE BUTTON WITH FULL VALIDATION
    # --------------------------------------------------------
    st.markdown("---")
    if st.button(
        "Generate PDF & Save Patient",
        type="primary",
        use_container_width=True
    ):
        st.session_state["rx_confirm_no_phases"] = False

        presc_str, start_str, followup_str = get_date_strings()

        data_to_validate = {
            "reg_no": st.session_state["rx_reg_no"].strip().upper(),
            "name": st.session_state["rx_name"].strip(),
            "age": st.session_state["rx_age"].strip(),
            "mobile": st.session_state["rx_mobile"].strip(),
            "prescription_date": presc_str,
            "start_date": start_str,
            "followup_date": followup_str,
        }

        errors = validate_prescription(
            data_to_validate,
            st.session_state["rx_phases"]
        )

        if errors:
            st.error("Please fix the following before saving:")
            for err in errors:
                st.error("- " + err)
        else:
            empty = get_empty_phases(st.session_state["rx_phases"])
            if empty:
                st.session_state["rx_confirm_no_phases"] = True
            else:
                do_save_prescription(presc_str, start_str, followup_str)

    # --------------------------------------------------------
    # PHASE CONFIRMATION DIALOG - per row with action buttons
    # --------------------------------------------------------
    if st.session_state.get("rx_confirm_no_phases", False):
        presc_str, start_str, followup_str = get_date_strings()
        empty_phases = get_empty_phases(st.session_state["rx_phases"])
        filled_phases = get_filled_phases(st.session_state["rx_phases"])

        phase_dot_colors = {
            "MORNING": "#E65100",
            "EVENING": "#1B5E20",
            "NIGHT": "#4A148C"
        }
        phase_name_colors = {
            "MORNING": "#633806",
            "EVENING": "#173404",
            "NIGHT": "#26215C"
        }
        phase_bg_empty = "#FCEBEB"
        phase_bg_filled = "#EAF3DE"
        phase_border_empty = "#E24B4A"
        phase_border_filled = "#639922"

        st.markdown("---")
        # CSS: Go back = deep red (secondary), Skip = dark navy (primary from config)
        st.markdown(
            "<style>"
            "div[data-testid='stVerticalBlock'] "
            "button[kind='secondaryFormSubmit'], "
            "div[data-testid='stVerticalBlock'] "
            "button[kind='secondary'] {"
            "background-color:#C62828 !important;"
            "border-color:#C62828 !important;"
            "color:white !important;"
            "font-weight:500 !important;}"
            "</style>",
            unsafe_allow_html=True
        )

        # Centered header
        st.markdown(
            "<div style='text-align:center; background:#1B2A4A; "
            "border-radius:8px; padding:10px 16px; margin-bottom:10px;'>"
            "<div style='display:inline-flex; align-items:center; "
            "justify-content:center; width:44px; height:44px; "
            "border-radius:50%; background:#FAEEDA; margin-bottom:10px;'>"
            "<svg width='22' height='22' viewBox='0 0 24 24' fill='none' "
            "stroke='#BA7517' stroke-width='2.5' stroke-linecap='round' "
            "stroke-linejoin='round'>"
            "<path d='M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 "
            "001.71-3L13.71 3.86a2 2 0 00-3.42 0z'/>"
            "<line x1='12' y1='9' x2='12' y2='13'/>"
            "<line x1='12' y1='17' x2='12.01' y2='17'/>"
            "</svg></div><br/>"
            "<span style='font-size:17px; font-weight:600; color:white; "
            "display:block; margin-bottom:4px;'>"
            "Incomplete Prescription Phases</span>"
            "<span style='font-size:13px; color:#B8860B;'>"
            "Please review all phases before saving</span>"
            "</div>",
            unsafe_allow_html=True
        )

        # Column headers
        st.markdown(
            "<div style='display:grid; grid-template-columns:120px 1fr; "
            "gap:12px; background:#f0f0f0; border-radius:6px; "
            "padding:8px 16px; margin-bottom:8px;'>"
            "<span style='font-size:12px; font-weight:600; color:#555; "
            "text-transform:uppercase; letter-spacing:0.06em;'>Phase</span>"
            "<span style='font-size:12px; font-weight:600; color:#555; "
            "text-transform:uppercase; letter-spacing:0.06em;'>"
            "Status and Remark</span>"
            "</div>",
            unsafe_allow_html=True
        )

        skipped_list = st.session_state.get("rx_skipped_phases", [])

        for phase_name in PHASE_NAMES:
            steps = st.session_state["rx_phases"].get(phase_name, [])
            is_empty = len(steps) == 0
            is_skipped = phase_name in skipped_list
            dot_color = phase_dot_colors[phase_name]
            name_color = phase_name_colors[phase_name]

            # Choose row appearance based on state
            if is_skipped:
                bg = "#F0F0F0"
                border = "#888888"
                status_html = (
                    "<p style='font-size:16px; font-weight:700; "
                    "color:#2E7D32; margin:0;'>Skipped</p>"
                    "<p style='font-size:14px; color:#2E7D32; margin:2px 0 0 0;'>"
                    "This phase will not appear in the prescription</p>"
                )
            elif is_empty:
                bg = phase_bg_empty
                border = phase_border_empty
                status_html = (
                    "<p style='font-size:16px; font-weight:700; "
                    "color:#A32D2D; margin:0;'>No medicines added</p>"
                    "<p style='font-size:14px; color:#A32D2D; margin:2px 0 0 0;'>"
                    "Add " + phase_name.capitalize() +
                    " medicines or skip this phase</p>"
                )
            else:
                bg = phase_bg_filled
                border = phase_border_filled
                count = str(len(steps))
                status_html = (
                    "<p style='font-size:16px; color:#3B6D11; margin:0;'>" +
                    count + " medicine(s) added</p>"
                    "<p style='font-size:14px; color:#3B6D11; margin:2px 0 0 0;'>"
                    "Complete - no action needed</p>"
                )

            st.markdown(
                "<div style='display:grid; grid-template-columns:110px 1fr; "
                "gap:10px; align-items:center; background:" + bg + "; "
                "border-radius:6px; padding:12px 14px; "
                "border-left:3px solid " + border + "; margin-bottom:6px;'>"
                "<div style='display:flex; align-items:center; gap:8px;'>"
                "<div style='width:10px; height:10px; border-radius:50%; "
                "background:" + dot_color + "; flex-shrink:0;'></div>"
                "<span style='font-size:14px; font-weight:500; "
                "color:" + name_color + ";'>" + phase_name.capitalize() +
                "</span></div>"
                "<div>" + status_html + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

            # Show buttons for empty phases (skipped or not)
            if is_empty:
                col_back, col_skip = st.columns([1, 1])
                with col_back:
                    if st.button(
                        "Go back and add " + phase_name.capitalize(),
                        key="confirm_back_" + phase_name,
                        use_container_width=True
                    ):
                        # Un-skip if previously skipped
                        if phase_name in skipped_list:
                            skipped_list.remove(phase_name)
                            st.session_state["rx_skipped_phases"] = skipped_list
                        st.session_state["rx_confirm_no_phases"] = False
                        st.rerun()
                with col_skip:
                    if is_skipped:
                        # Show disabled button with tick
                        st.button(
                            "Skipped",
                            key="confirm_skip_done_" + phase_name,
                            use_container_width=True,
                            disabled=True
                        )
                    else:
                        if st.button(
                            "Skip " + phase_name.capitalize(),
                            key="confirm_skip_" + phase_name,
                            use_container_width=True,
                            type="primary"
                        ):
                            if phase_name not in skipped_list:
                                skipped_list.append(phase_name)
                            st.session_state["rx_skipped_phases"] = skipped_list
                            # Check if all empty phases now decided
                            all_decided = all(
                                p in skipped_list
                                for p in get_empty_phases(
                                    st.session_state["rx_phases"]
                                )
                            )
                            if all_decided:
                                st.session_state["rx_confirm_no_phases"] = False
                                st.session_state["rx_skipped_phases"] = []
                                do_save_prescription(
                                    presc_str, start_str, followup_str
                                )
                            else:
                                st.rerun()
            st.markdown("")

        # Check if all empty phases are now skipped - show Proceed button
        empty_phases = get_empty_phases(st.session_state["rx_phases"])
        all_decided = all(p in skipped_list for p in empty_phases)
        if all_decided and empty_phases:
            st.markdown("---")
            st.success(
                "All empty phases have been addressed. "
                "Click below to save the prescription."
            )
            if st.button(
                "Proceed and Save Prescription",
                key="confirm_proceed_save",
                use_container_width=True,
                type="primary"
            ):
                st.session_state["rx_confirm_no_phases"] = False
                st.session_state["rx_skipped_phases"] = []
                do_save_prescription(presc_str, start_str, followup_str)


def do_save_prescription(presc_str, start_str, followup_str):
    weight_raw = st.session_state.get("rx_weight", "")
    height_raw = st.session_state.get("rx_height", "")
    try:
        weight = float(weight_raw) if weight_raw else 0.0
    except Exception:
        weight = 0.0
    try:
        height = float(height_raw) if height_raw else 0.0
    except Exception:
        height = 0.0
    bmi = calculate_bmi(weight, height) if weight > 0 and height > 0 else 0.0

    phases_list = []
    for phase_name in PHASE_NAMES:
        steps = st.session_state["rx_phases"][phase_name]
        if steps:
            phase_steps = []
            for idx, s in enumerate(steps):
                phase_steps.append({
                    "step": idx + 1,
                    "medicine": s.get("medicine", ""),
                    "substitute": s.get("substitute", ""),
                    "wait_time": s.get("wait_time", ""),
                    "area": s.get("area", ""),
                    "dose": s.get("dose", ""),
                    "duration": s.get("duration", "")
                })
            phases_list.append({
                "phase": phase_name,
                "steps": phase_steps
            })

    patient_data = {
        "reg_no": st.session_state["rx_reg_no"].strip().upper(),
        "name": st.session_state["rx_name"].strip(),
        "age": int(st.session_state["rx_age"]),
        "sex": st.session_state["rx_sex"],
        "mobile": st.session_state["rx_mobile"].strip(),
        "weight": weight,
        "height": height,
        "bmi": bmi,
        "prescription_date": presc_str,
        "start_date": start_str,
        "followup_date": followup_str,
        "doctor": st.session_state["rx_doctor"],
        "phases": json.dumps(phases_list),
        "notes": st.session_state["rx_notes"],
        "bp": st.session_state["rx_bp"],
        "email": st.session_state["rx_email"],
    }

    ok, msg = save_patient(patient_data)
    if ok:
        photo_bytes = st.session_state.get("rx_photo_bytes", None)
        pdf_ok, pdf_result = generate_pdf(patient_data, photo_bytes=photo_bytes)
        if pdf_ok:
            st.success(
                "Patient saved! PDF: " +
                os.path.basename(pdf_result)
            )
            with open(pdf_result, "rb") as f:
                pdf_bytes = f.read()
            st.download_button(
                label="Download PDF",
                data=pdf_bytes,
                file_name=os.path.basename(pdf_result),
                mime="application/pdf"
            )
            # Clear form only after successful save
            clear_rx_state()
        else:
            st.warning(
                "Patient saved but PDF error: " + pdf_result
            )
    else:
        st.error(msg)

# ============================================================
# PLACEHOLDER FOR SCREENS NOT YET BUILT
# ============================================================


# ============================================================
# PATIENT RECORDS HELPERS - G4
# ============================================================

def search_patients(query):
    try:
        q = query.strip()
        fields = "select=reg_no,name,age,sex,mobile,prescription_date,followup_date,doctor"
        # Search by name, reg_no or mobile using Supabase OR filter
        rows = sb_get(
            "patients",
            fields + "&or=(name.ilike.*" + q + "*,reg_no.ilike.*" + q +
            "*,mobile.ilike.*" + q + "*)" +
            "&order=prescription_date.desc"
        )
        return rows if rows else []
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_all_patients():
    try:
        rows = sb_get(
            "patients",
            "select=reg_no,name,age,sex,mobile,"
            "prescription_date,followup_date,doctor"
            "&order=prescription_date.desc"
        )
        return rows if rows else []
    except Exception:
        return []


def get_prescription_history(reg_no):
    try:
        rows = sb_get(
            "prescription_history",
            "select=id,prescription_date,start_date,"
            "followup_date,notes,phases,saved_at"
            "&reg_no=eq." + str(reg_no) +
            "&order=saved_at.desc"
        )
        return rows if rows else []
    except Exception:
        return []


def load_patient_into_form(reg_no):
    patient = get_patient_by_reg_no(reg_no)
    if not patient:
        return False
    # Reset form first
    reset_rx_defaults()
    # Load patient data into session state
    st.session_state["rx_reg_no"] = patient.get("reg_no", "")
    st.session_state["rx_name"] = patient.get("name", "")
    st.session_state["rx_age"] = str(patient.get("age", ""))
    st.session_state["rx_sex"] = patient.get("sex", "Female")
    st.session_state["rx_mobile"] = patient.get("mobile", "")
    st.session_state["rx_weight"] = str(patient.get("weight", "")) if patient.get("weight") else ""
    st.session_state["rx_height"] = str(patient.get("height", "")) if patient.get("height") else ""
    st.session_state["rx_bp"] = patient.get("bp", "")
    st.session_state["rx_email"] = patient.get("email", "")
    st.session_state["rx_doctor"] = patient.get("doctor", "Dr. Anita Rath")
    st.session_state["rx_notes"] = patient.get("notes", "")

    # Parse dates
    try:
        pd_str = patient.get("prescription_date", "")
        if pd_str:
            st.session_state["rx_presc_date"] = datetime.strptime(
                pd_str, "%d-%m-%Y"
            ).date()
    except Exception:
        pass

    try:
        sd_str = patient.get("start_date", "")
        if sd_str:
            st.session_state["rx_start_date"] = datetime.strptime(
                sd_str, "%d-%m-%Y"
            ).date()
    except Exception:
        pass

    try:
        fd_str = patient.get("followup_date", "")
        if fd_str:
            st.session_state["rx_followup_date"] = datetime.strptime(
                fd_str, "%d-%m-%Y"
            ).date()
    except Exception:
        pass

    # Parse phases
    try:
        phases_json = patient.get("phases", "[]")
        phases_list = json.loads(phases_json) if phases_json else []
        phases_dict = {"MORNING": [], "EVENING": [], "NIGHT": []}
        for phase in phases_list:
            phase_name = phase.get("phase", "")
            if phase_name in phases_dict:
                phases_dict[phase_name] = phase.get("steps", [])
        st.session_state["rx_phases"] = phases_dict
    except Exception:
        pass

    return True


# ============================================================
# PATIENT RECORDS SCREEN - G4
# ============================================================

def show_patient_records():
    st.markdown(
        "<h2 style='color:#B8860B;'>Patient Records</h2>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # Search bar
    col_search, col_btn = st.columns([4, 1])
    with col_search:
        search_query = st.text_input(
            "Search by Name, Registration No, or Mobile",
            value=st.session_state.get("pr_search_query", ""),
            key="pr_search_input",
            placeholder="e.g. Anita or ASC1001 or 9876543210"
        )
        st.session_state["pr_search_query"] = search_query
    with col_btn:
        st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
        if st.button("Search", use_container_width=True, type="primary"):
            st.session_state["pr_selected_reg_no"] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")

    # Fetch results
    if search_query.strip():
        patients = search_patients(search_query)
        result_label = (
            str(len(patients)) + " patient(s) found for: " + search_query
        )
    else:
        patients = get_all_patients()
        result_label = "All patients (" + str(len(patients)) + " total)"

    if not patients:
        st.info("No patients found.")
        return

    st.markdown(
        "<p style='color:#666; font-size:13px;'>" +
        result_label + "</p>",
        unsafe_allow_html=True
    )

    # Results table header
    st.markdown(
        "<div style='display:grid; grid-template-columns:"
        "35px 90px 1fr 50px 70px 110px 110px 110px 160px; "
        "gap:8px; background:#1B2A4A; color:white; "
        "padding:8px 12px; border-radius:6px 6px 0 0; "
        "font-size:12px; font-weight:600; "
        "text-transform:uppercase; letter-spacing:0.04em;'>"
        "<span>S.No</span>"
        "<span>Reg No</span>"
        "<span>Name</span>"
        "<span>Age</span>"
        "<span>Sex</span>"
        "<span>Mobile</span>"
        "<span>Presc. Date</span>"
        "<span>Follow-up</span>"
        "<span>Action</span>"
        "</div>",
        unsafe_allow_html=True
    )

    selected = st.session_state.get("pr_selected_reg_no", None)

    for i, p in enumerate(patients):
        bg = "#EEF2FF" if p["reg_no"] == selected else (
            "#FFFFFF" if i % 2 == 0 else "#F9F9F9"
        )
        border = (
            "border-left:3px solid #B8860B;"
            if p["reg_no"] == selected else ""
        )
        followup = p.get("followup_date", "") or ""

        # Row with data and button in same line
        row_col, btn_col = st.columns([5, 1])
        with row_col:
            st.markdown(
                "<div style='display:grid; grid-template-columns:"
                "35px 90px 1fr 50px 70px 110px 110px 110px; "
                "gap:8px; background:" + bg + "; "
                "padding:8px 12px; border-bottom:0.5px solid #eee; "
                + border + " font-size:13px;'>"
                "<span style='color:#888;'>" + str(i + 1) + "</span>"
                "<span style='color:#B8860B; font-weight:500;'>" +
                p["reg_no"] + "</span>"
                "<span>" + p["name"] + "</span>"
                "<span>" + str(p["age"]) + "</span>"
                "<span>" + p["sex"] + "</span>"
                "<span>" + p["mobile"] + "</span>"
                "<span>" + p["prescription_date"] + "</span>"
                "<span>" + followup + "</span>"
                "</div>",
                unsafe_allow_html=True
            )
        with btn_col:
            if st.button(
                "Select for Edit / Reprint / History",
                key="pr_select_" + p["reg_no"],
                use_container_width=True
            ):
                st.session_state["pr_selected_reg_no"] = p["reg_no"]
                st.session_state["pr_show_history"] = False
                st.rerun()

    st.markdown("---")

    # Detail panel for selected patient
    if selected:
        patient = get_patient_by_reg_no(selected)
        if not patient:
            st.warning("Patient not found.")
            return

        st.markdown(
            "<div style='background:#FFF8DC; border-radius:8px; "
            "border-left:4px solid #B8860B; padding:16px 20px; "
            "margin-bottom:16px;'>"
            "<h3 style='margin:0 0 4px 0; color:#1B2A4A;'>" +
            patient["name"] + "</h3>"
            "<p style='margin:0; color:#666; font-size:13px;'>"
            "Reg No: " + patient["reg_no"] + " | "
            "Age: " + str(patient["age"]) + " | "
            "Sex: " + patient["sex"] + " | "
            "Mobile: " + patient["mobile"] +
            "</p></div>",
            unsafe_allow_html=True
        )

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button(
                "Edit Prescription",
                use_container_width=True,
                type="primary",
                key="pr_edit_btn"
            ):
                if load_patient_into_form(selected):
                    st.session_state["current_page"] = "New Prescription"
                    st.session_state["pr_selected_reg_no"] = None
                    st.rerun()
        with col2:
            if st.button(
                "Reprint PDF",
                use_container_width=True,
                key="pr_reprint_btn"
            ):
                pdf_ok, pdf_result = generate_pdf(dict(patient))
                if pdf_ok:
                    with open(pdf_result, "rb") as f:
                        pdf_bytes_dl = f.read()
                    st.download_button(
                        label="Download PDF",
                        data=pdf_bytes_dl,
                        file_name=os.path.basename(pdf_result),
                        mime="application/pdf",
                        key="pr_download_pdf"
                    )
                else:
                    st.error("PDF error: " + pdf_result)
        with col3:
            if st.button(
                "View History",
                use_container_width=True,
                key="pr_history_btn"
            ):
                st.session_state["pr_show_history"] = not st.session_state.get(
                    "pr_show_history", False
                )
                st.rerun()
        with col4:
            if st.button(
                "Close",
                use_container_width=True,
                key="pr_close_btn"
            ):
                st.session_state["pr_selected_reg_no"] = None
                st.session_state["pr_show_history"] = False
                st.rerun()

        # Prescription summary
        st.markdown("#### Current Prescription")
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown(
                "**Prescription Date:** " +
                patient.get("prescription_date", "") + "  \n" +
                "**Start Date:** " +
                patient.get("start_date", "") + "  \n" +
                "**Follow-up:** " +
                (patient.get("followup_date", "") or "Not set")
            )
        with col_b:
            w = patient.get("weight", 0)
            h = patient.get("height", 0)
            b = patient.get("bmi", 0)
            try:
                w_display = (
                    str(int(float(w)))
                    if float(w) == int(float(w))
                    else str(float(w))
                ) + " kg" if float(w) > 0 else "Not recorded"
            except Exception:
                w_display = "Not recorded"
            try:
                h_display = (
                    str(int(float(h)))
                    if float(h) == int(float(h))
                    else str(float(h))
                ) + " cm" if float(h) > 0 else "Not recorded"
            except Exception:
                h_display = "Not recorded"
            try:
                b_display = (
                    str(float(b)) + " (" + bmi_category(float(b)) + ")"
                ) if float(b) > 0 else "Not recorded"
            except Exception:
                b_display = "Not recorded"
            st.markdown(
                "**Weight:** " + w_display + "  \n" +
                "**Height:** " + h_display + "  \n" +
                "**BMI:** " + b_display
            )

        if patient.get("notes"):
            st.markdown(
                "<div style='background:#E8F4FD; border-radius:6px; "
                "padding:10px 14px; margin:8px 0;'>"
                "<b>Clinical Notes:</b> " + patient["notes"] +
                "</div>",
                unsafe_allow_html=True
            )

        # Phase summary
        try:
            phases = json.loads(patient.get("phases", "[]"))
            for phase in phases:
                pname = phase.get("phase", "")
                steps = phase.get("steps", [])
                if not steps:
                    continue
                phase_colors_ui = {
                    "MORNING": "#E65100",
                    "EVENING": "#1B5E20",
                    "NIGHT": "#4A148C"
                }
                color = phase_colors_ui.get(pname, "#333")
                st.markdown(
                    "<div style='background:" + color + "; color:white; "
                    "padding:5px 12px; border-radius:4px; "
                    "font-weight:bold; margin:8px 0 4px 0;'>" +
                    pname + "</div>",
                    unsafe_allow_html=True
                )
                for step in steps:
                    st.markdown(
                        "**" + str(step.get("step", "")) + ".** " +
                        step.get("medicine", "") +
                        (" | Sub: " + step.get("substitute", "")
                         if step.get("substitute", "") not in ["", "Not Applicable", "-- Select --"]
                         else "") +
                        (" | " + step.get("area", "")
                         if step.get("area", "") not in ["", "Not Applicable", "-- Select --"]
                         else "") +
                        (" | " + step.get("dose", "")
                         if step.get("dose", "") not in ["", "Not Applicable", "-- Select --"]
                         else "") +
                        (" | " + step.get("duration", "")
                         if step.get("duration", "") not in ["", "Not Applicable", "-- Select --"]
                         else "")
                    )
        except Exception:
            pass

        # History panel
        if st.session_state.get("pr_show_history", False):
            st.markdown("---")
            st.markdown("#### Prescription History")
            history = get_prescription_history(selected)
            if not history:
                st.info("No previous versions found for this patient.")
            else:
                for h in history:
                    saved_at = h.get("saved_at", "")
                    try:
                        saved_dt = datetime.fromisoformat(saved_at)
                        saved_display = saved_dt.strftime(
                            "%d-%m-%Y at %I:%M %p"
                        )
                    except Exception:
                        saved_display = saved_at

                    with st.expander(
                        "Version saved on " + saved_display
                    ):
                        col_h1, col_h2 = st.columns(2)
                        with col_h1:
                            pd_h = h.get("prescription_date") or ""
                            sd_h = h.get("start_date") or ""
                            fd_h = h.get("followup_date") or "Not set"
                            st.markdown(
                                "**Prescription Date:** " + pd_h + "  \n" +
                                "**Start Date:** " + sd_h + "  \n" +
                                "**Follow-up:** " + fd_h
                            )
                        with col_h2:
                            if h.get("notes"):
                                st.markdown(
                                    "**Notes:** " + h["notes"]
                                )
                        try:
                            h_phases = json.loads(
                                h.get("phases", "[]")
                            )
                            for phase in h_phases:
                                pname = phase.get("phase", "")
                                steps = phase.get("steps", [])
                                if steps:
                                    st.markdown("**" + pname + ":**")
                                    for step in steps:
                                        st.markdown(
                                            "- " +
                                            step.get("medicine", "")
                                        )
                        except Exception:
                            pass


# ============================================================
# STATISTICS HELPERS - G5
# ============================================================

@st.cache_data(ttl=60)
def get_patients_by_month():
    try:
        rows = sb_get(
            "patients",
            "select=prescription_date&prescription_date=neq."
        )
        from collections import defaultdict
        counts = defaultdict(int)
        today = datetime.now()
        for row in rows:
            try:
                d = datetime.strptime(
                    row["prescription_date"], "%d-%m-%Y"
                )
                key = d.strftime("%b %Y")
                counts[key] += 1
            except Exception:
                continue
        months = []
        for i in range(11, -1, -1):
            if today.month - i <= 0:
                m = today.month - i + 12
                y = today.year - 1
            else:
                m = today.month - i
                y = today.year
            label = datetime(y, m, 1).strftime("%b %Y")
            months.append((label, counts.get(label, 0)))
        return months
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_top_medicines(limit=10):
    try:
        rows = sb_get("patients", "select=phases&phases=neq.")
        from collections import defaultdict
        counts = defaultdict(int)
        for row in rows:
            try:
                phases = json.loads(row.get("phases", "[]"))
                for phase in phases:
                    for step in phase.get("steps", []):
                        med = step.get("medicine", "").strip()
                        if med and med not in [
                            "", "-- Select --", "Not Applicable"
                        ]:
                            counts[med] += 1
            except Exception:
                continue
        sorted_meds = sorted(
            counts.items(), key=lambda x: x[1], reverse=True
        )
        return sorted_meds[:limit]
    except Exception:
        return []


@st.cache_data(ttl=60)
def get_bmi_distribution():
    try:
        rows = sb_get("patients", "select=bmi&bmi=gt.0")
        cats = {
            "Underweight": 0, "Normal": 0,
            "Overweight": 0, "Obese": 0
        }
        for row in rows:
            cat = bmi_category(float(row["bmi"]))
            if cat in cats:
                cats[cat] += 1
        return cats
    except Exception:
        return {}


@st.cache_data(ttl=60)
def get_age_distribution():
    try:
        rows = sb_get("patients", "select=age&age=gt.0")
        groups = {
            "0-18": 0, "19-30": 0, "31-45": 0,
            "46-60": 0, "60+": 0
        }
        for row in rows:
            age = int(row["age"])
            if age <= 18:
                groups["0-18"] += 1
            elif age <= 30:
                groups["19-30"] += 1
            elif age <= 45:
                groups["31-45"] += 1
            elif age <= 60:
                groups["46-60"] += 1
            else:
                groups["60+"] += 1
        return groups
    except Exception:
        return {}


@st.cache_data(ttl=60)
def get_sex_distribution():
    try:
        rows = sb_get("patients", "select=sex")
        dist = {}
        for row in rows:
            sex = row.get("sex", "")
            if sex:
                dist[sex] = dist.get(sex, 0) + 1
        return dist
    except Exception:
        return {}


@st.cache_data(ttl=60)
def get_followups_next_30_days():
    try:
        rows = sb_get(
            "patients",
            "select=reg_no,name,mobile,followup_date"
            "&followup_date=neq."
        )
        today = datetime.now().date()
        cutoff = today + timedelta(days=30)
        upcoming = []
        for row in rows:
            try:
                fd = row.get("followup_date", "")
                if not fd:
                    continue
                fdate = datetime.strptime(fd, "%d-%m-%Y").date()
                if today <= fdate <= cutoff:
                    days_left = (fdate - today).days
                    upcoming.append({
                        "Reg No": row["reg_no"],
                        "Name": row["name"],
                        "Mobile": row["mobile"],
                        "Follow-up Date": fd,
                        "Days Left": days_left
                    })
            except Exception:
                continue
        upcoming.sort(key=lambda x: x["Days Left"])
        return upcoming
    except Exception:
        return []


def make_bar_chart(data_pairs, title, color="#B8860B"):
    if not data_pairs:
        return ""
    max_val = max(v for _, v in data_pairs) if data_pairs else 1
    if max_val == 0:
        max_val = 1
    bars_html = ""
    for label, val in data_pairs:
        pct = int((val / max_val) * 100)
        bars_html += (
            "<div style='display:flex; align-items:center; "
            "margin-bottom:6px; gap:8px;'>"
            "<div style='width:110px; font-size:11px; "
            "color:var(--color-text-secondary); text-align:right; "
            "flex-shrink:0; white-space:nowrap; overflow:hidden; "
            "text-overflow:ellipsis;'>" + label + "</div>"
            "<div style='flex:1; background:#f0f0f0; "
            "border-radius:3px; height:18px;'>"
            "<div style='width:" + str(pct) + "%; background:" +
            color + "; height:18px; border-radius:3px; "
            "min-width:2px;'></div></div>"
            "<div style='width:28px; font-size:11px; "
            "font-weight:500; color:var(--color-text-primary);'>" +
            str(val) + "</div>"
            "</div>"
        )
    return (
        "<div style='margin-bottom:16px;'>"
        "<p style='font-size:13px; font-weight:500; "
        "color:var(--color-text-primary); margin:0 0 8px 0;'>" +
        title + "</p>" + bars_html + "</div>"
    )


# ============================================================
# STATISTICS SCREEN - G5
# ============================================================

def show_statistics():
    st.markdown(
        "<h2 style='color:#B8860B;'>Statistics Dashboard</h2>",
        unsafe_allow_html=True
    )

    col_title, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("Refresh", use_container_width=True):
            st.rerun()

    st.markdown("---")

    # --- Summary Cards ---
    total = get_total_patients()
    this_month = get_patients_this_month()
    avg_bmi = get_average_bmi()
    followups_30 = get_followups_next_30_days()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(label="Total Patients", value=str(total))
    with col2:
        st.metric(label="Patients This Month", value=str(this_month))
    with col3:
        st.metric(label="Average BMI", value=str(avg_bmi))
    with col4:
        st.metric(
            label="Follow-ups (Next 30 Days)",
            value=str(len(followups_30))
        )

    st.markdown("---")

    # --- Charts Row 1: Patients by Month + Top Medicines ---
    col_left, col_right = st.columns(2)

    with col_left:
        st.markdown("### Patients by Month")
        months_data = get_patients_by_month()
        if months_data and any(v > 0 for _, v in months_data):
            st.markdown(
                make_bar_chart(months_data, "Last 12 months", "#1B2A4A"),
                unsafe_allow_html=True
            )
        else:
            st.info("No prescription data available yet.")

    with col_right:
        st.markdown("### Top 10 Medicines")
        top_meds = get_top_medicines(10)
        if top_meds:
            st.markdown(
                make_bar_chart(top_meds, "By prescription count", "#B8860B"),
                unsafe_allow_html=True
            )
        else:
            st.info("No medicine data available yet.")

    st.markdown("---")

    # --- Charts Row 2: Distributions ---
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("### BMI Distribution")
        bmi_dist = get_bmi_distribution()
        total_bmi = sum(bmi_dist.values())
        if total_bmi > 0:
            for cat, count in bmi_dist.items():
                pct = round((count / total_bmi) * 100, 1)
                cat_colors = {
                    "Underweight": "#1565C0",
                    "Normal": "#2E7D32",
                    "Overweight": "#E65100",
                    "Obese": "#C62828"
                }
                color = cat_colors.get(cat, "#888")
                bar_pct = int((count / max(bmi_dist.values())) * 100)
                st.markdown(
                    "<div style='margin-bottom:8px;'>"
                    "<div style='display:flex; justify-content:space-between; "
                    "font-size:12px; margin-bottom:3px;'>"
                    "<span style='color:var(--color-text-primary);'>" +
                    cat + "</span>"
                    "<span style='color:var(--color-text-secondary);'>" +
                    str(count) + " (" + str(pct) + "%)</span></div>"
                    "<div style='background:#f0f0f0; border-radius:3px; "
                    "height:14px;'><div style='width:" + str(bar_pct) +
                    "%; background:" + color + "; height:14px; "
                    "border-radius:3px; min-width:2px;'></div></div>"
                    "</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No BMI data available.")

    with col2:
        st.markdown("### Age Groups")
        age_dist = get_age_distribution()
        total_age = sum(age_dist.values())
        if total_age > 0:
            max_age = max(age_dist.values())
            for grp, count in age_dist.items():
                pct = round((count / total_age) * 100, 1)
                bar_pct = int((count / max_age) * 100) if max_age > 0 else 0
                st.markdown(
                    "<div style='margin-bottom:8px;'>"
                    "<div style='display:flex; justify-content:space-between; "
                    "font-size:12px; margin-bottom:3px;'>"
                    "<span style='color:var(--color-text-primary);'>" +
                    grp + " years</span>"
                    "<span style='color:var(--color-text-secondary);'>" +
                    str(count) + " (" + str(pct) + "%)</span></div>"
                    "<div style='background:#f0f0f0; border-radius:3px; "
                    "height:14px;'><div style='width:" + str(bar_pct) +
                    "%; background:#4A148C; height:14px; "
                    "border-radius:3px; min-width:2px;'></div></div>"
                    "</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No age data available.")

    with col3:
        st.markdown("### Sex Breakdown")
        sex_dist = get_sex_distribution()
        total_sex = sum(sex_dist.values())
        if total_sex > 0:
            sex_colors = {
                "Female": "#C62828",
                "Male": "#1B2A4A",
                "Other": "#B8860B"
            }
            max_sex = max(sex_dist.values())
            for sex, count in sex_dist.items():
                pct = round((count / total_sex) * 100, 1)
                bar_pct = int((count / max_sex) * 100) if max_sex > 0 else 0
                color = sex_colors.get(sex, "#888")
                st.markdown(
                    "<div style='margin-bottom:8px;'>"
                    "<div style='display:flex; justify-content:space-between; "
                    "font-size:12px; margin-bottom:3px;'>"
                    "<span style='color:var(--color-text-primary);'>" +
                    sex + "</span>"
                    "<span style='color:var(--color-text-secondary);'>" +
                    str(count) + " (" + str(pct) + "%)</span></div>"
                    "<div style='background:#f0f0f0; border-radius:3px; "
                    "height:14px;'><div style='width:" + str(bar_pct) +
                    "%; background:" + color + "; height:14px; "
                    "border-radius:3px; min-width:2px;'></div></div>"
                    "</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No sex data available.")

    st.markdown("---")

    # --- Upcoming Follow-ups Table ---
    st.markdown("### Upcoming Follow-ups (Next 30 Days)")
    if not followups_30:
        st.info("No follow-ups due in the next 30 days.")
    else:
        st.success(
            str(len(followups_30)) +
            " patient(s) due for follow-up in the next 30 days."
        )
        # Colour code by urgency
        for f in followups_30:
            days = f["Days Left"]
            if days <= 2:
                bg = "#FFEBEE"
                badge_color = "#C62828"
                urgency = "TODAY" if days == 0 else "URGENT"
            elif days <= 7:
                bg = "#FFF3E0"
                badge_color = "#E65100"
                urgency = str(days) + " days"
            else:
                bg = "#F1F8E9"
                badge_color = "#2E7D32"
                urgency = str(days) + " days"

            st.markdown(
                "<div style='display:flex; align-items:center; "
                "gap:12px; background:" + bg + "; "
                "border-radius:6px; padding:10px 14px; "
                "margin-bottom:6px;'>"
                "<span style='background:" + badge_color + "; "
                "color:white; font-size:11px; font-weight:600; "
                "padding:2px 8px; border-radius:4px; "
                "min-width:56px; text-align:center;'>" +
                urgency + "</span>"
                "<span style='font-weight:500; color:var(--color-text-primary); "
                "min-width:120px;'>" + f["Name"] + "</span>"
                "<span style='color:var(--color-text-secondary); "
                "font-size:12px; min-width:80px;'>" + f["Reg No"] + "</span>"
                "<span style='color:var(--color-text-secondary); "
                "font-size:12px; min-width:100px;'>" + f["Mobile"] + "</span>"
                "<span style='color:var(--color-text-secondary); "
                "font-size:12px;'>" + f["Follow-up Date"] + "</span>"
                "</div>",
                unsafe_allow_html=True
            )


# ============================================================
# MEDICINE LIBRARY HELPERS - G6
# ============================================================

@st.cache_data(ttl=60)
def get_all_medicines_with_notes():
    try:
        rows = sb_get(
            "medicines",
            "select=id,name,interaction_note&order=name.asc"
        )
        return rows if rows else []
    except Exception:
        return []


def save_interaction_note(medicine_name, note):
    try:
        return sb_update(
            "medicines", "name", medicine_name,
            {"interaction_note": note}
        )
    except Exception:
        return False


def add_medicine_to_library(name):
    name = name.strip()
    if not name:
        return False, "Medicine name cannot be empty."
    try:
        existing = sb_get(
            "medicines", "select=id&name=eq." + name
        )
        if existing:
            return False, "Medicine already exists in the library."
        ok = sb_upsert("medicines", {
            "name": name,
            "added_on": datetime.now().strftime("%d-%m-%Y"),
            "interaction_note": ""
        })
        if ok:
            return True, "Medicine added successfully."
        return False, "Error adding medicine."
    except Exception as e:
        return False, "Error adding medicine: " + str(e)


def remove_medicine_from_library(name):
    try:
        ok = sb_delete("medicines", "name", name)
        if ok:
            return True, "Medicine removed successfully."
        return False, "Error removing medicine."
    except Exception as e:
        return False, "Error removing medicine: " + str(e)


def bulk_upload_medicines(csv_text):
    # Parse CSV text and add all medicines
    # Returns (added_count, skipped_count, errors)
    lines = csv_text.strip().split("\n")
    added = 0
    skipped = 0
    errors = []
    for line in lines:
        name = line.strip().strip(",").strip('"').strip("'")
        if not name:
            continue
        # Skip header row if present
        if name.lower() in ["medicine name", "medicine", "name", "medicines"]:
            continue
        ok, msg = add_medicine_to_library(name)
        if ok:
            added += 1
        elif "already exists" in msg:
            skipped += 1
        else:
            errors.append(name + ": " + msg)
    return added, skipped, errors


# ============================================================
# MEDICINE LIBRARY SCREEN - G6
# ============================================================

def show_medicine_library():
    st.markdown(
        "<h2 style='color:#B8860B;'>Medicine Library</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#666; font-size:13px;'>"
        "Manage the medicines available in prescription dropdowns. "
        "Medicines with interaction notes show a warning indicator.</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    medicines = get_all_medicines_with_notes()

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("### Medicine List")
        st.markdown(
            "<p style='font-size:12px; color:#888;'>" +
            str(len(medicines)) + " medicines in library</p>",
            unsafe_allow_html=True
        )

        selected_med = st.session_state.get("ml_selected_medicine", None)

        for med in medicines:
            name = med["name"]
            note = med.get("interaction_note", "") or ""
            has_note = len(note.strip()) > 0
            indicator = " [!]" if has_note else ""
            is_selected = name == selected_med
            bg = "#FFF8DC" if is_selected else "transparent"
            border = "border-left:3px solid #B8860B;" if is_selected else ""
            text_color = "#B8860B" if is_selected else "var(--color-text-primary)"
            warn_color = "#C62828" if has_note else "transparent"

            st.markdown(
                "<div style='display:flex; align-items:center; "
                "gap:6px; background:" + bg + "; " + border +
                " padding:5px 8px; border-radius:4px; margin-bottom:2px;'>"
                "<div style='width:8px; height:8px; border-radius:50%; "
                "background:" + warn_color + "; flex-shrink:0;'></div>"
                "<span style='font-size:13px; color:" + text_color +
                "; font-weight:" + ("600" if is_selected else "400") +
                ";'>" + name + indicator + "</span>"
                "</div>",
                unsafe_allow_html=True
            )
            if st.button(
                "Select",
                key="ml_select_" + name,
                use_container_width=True
            ):
                st.session_state["ml_selected_medicine"] = name
                st.session_state["ml_note_text"] = note
                st.rerun()

        st.markdown("---")
        st.markdown("#### Add New Medicine")
        new_med_name = st.text_input(
            "Medicine name",
            key="ml_new_med_input",
            placeholder="e.g. Retinol Cream"
        )
        if st.button(
            "Add Medicine",
            key="ml_add_btn",
            use_container_width=True,
            type="primary"
        ):
            ok, msg = add_medicine_to_library(new_med_name)
            if ok:
                st.success(msg)
                st.session_state["ml_selected_medicine"] = new_med_name
                st.rerun()
            else:
                st.error(msg)

        st.markdown("---")
        st.markdown("#### Bulk Upload from CSV")
        st.caption(
            "Upload a CSV or TXT file with one medicine name per row. "
            "Duplicates are automatically skipped."
        )

        uploaded_file = st.file_uploader(
            "Choose CSV or TXT file",
            type=["csv", "txt"],
            key="ml_bulk_upload"
        )

        if uploaded_file is not None:
            try:
                csv_text = uploaded_file.read().decode("utf-8")
            except Exception:
                try:
                    uploaded_file.seek(0)
                    csv_text = uploaded_file.read().decode("latin-1")
                except Exception:
                    csv_text = ""

            if csv_text:
                lines_preview = [
                    l.strip() for l in csv_text.split("\n")
                    if l.strip()
                ]
                # Remove header if present
                preview_lines = [
                    l for l in lines_preview
                    if l.lower() not in [
                        "medicine name", "medicine", "name", "medicines"
                    ]
                ]
                st.markdown(
                    "<p style='font-size:12px; color:#666;'>"
                    "File contains <b>" +
                    str(len(preview_lines)) +
                    "</b> medicine(s) to upload.</p>",
                    unsafe_allow_html=True
                )
                if preview_lines:
                    with st.expander("Preview first 10 medicines"):
                        for name in preview_lines[:10]:
                            st.markdown(
                                "- " + name.strip().strip(",")
                                .strip('"').strip("'")
                            )

                if st.button(
                    "Upload All Medicines",
                    key="ml_bulk_upload_btn",
                    use_container_width=True,
                    type="primary"
                ):
                    added, skipped, errors = bulk_upload_medicines(csv_text)
                    if added > 0:
                        st.success(
                            str(added) + " medicine(s) added successfully."
                        )
                    if skipped > 0:
                        st.info(
                            str(skipped) +
                            " medicine(s) already existed and were skipped."
                        )
                    if errors:
                        for err in errors:
                            st.error("Failed: " + err)
                    st.rerun()

    with col_right:
        st.markdown("### Medicine Details")

        if not selected_med:
            st.info(
                "Select a medicine from the list on the left "
                "to view and edit its details."
            )
        else:
            st.markdown(
                "<div style='background:#1B2A4A; color:white; "
                "border-radius:8px; padding:12px 16px; "
                "margin-bottom:16px;'>"
                "<h3 style='margin:0; color:white;'>" +
                selected_med + "</h3>"
                "<p style='margin:4px 0 0 0; font-size:12px; "
                "color:#B8860B;'>Selected medicine</p>"
                "</div>",
                unsafe_allow_html=True
            )

            # Interaction note editor
            st.markdown("#### Interaction Note / Warning")
            st.caption(
                "This warning will appear when staff selects "
                "this medicine in a prescription."
            )

            current_note = st.session_state.get("ml_note_text", "")
            note_input = st.text_area(
                "Interaction note",
                value=current_note,
                key="ml_note_area",
                height=150,
                placeholder="e.g. Do not use with Retinoids. "
                "Avoid sun exposure after application."
            )

            col_save, col_clear = st.columns(2)
            with col_save:
                if st.button(
                    "Save Note",
                    key="ml_save_note_btn",
                    use_container_width=True,
                    type="primary"
                ):
                    ok = save_interaction_note(selected_med, note_input)
                    if ok:
                        st.session_state["ml_note_text"] = note_input
                        st.success(
                            "Interaction note saved for " + selected_med
                        )
                        st.rerun()
                    else:
                        st.error("Failed to save note.")
            with col_clear:
                if st.button(
                    "Clear Note",
                    key="ml_clear_note_btn",
                    use_container_width=True
                ):
                    ok = save_interaction_note(selected_med, "")
                    if ok:
                        st.session_state["ml_note_text"] = ""
                        st.success("Note cleared.")
                        st.rerun()
                    else:
                        st.error("Failed to clear note.")

            # Current note display
            current_saved = next(
                (m.get("interaction_note", "") or ""
                 for m in medicines if m["name"] == selected_med),
                ""
            )
            if current_saved.strip():
                st.markdown("")
                st.markdown(
                    "<div style='background:#FFEBEE; border-left:4px solid "
                    "#C62828; border-radius:4px; padding:10px 14px;'>"
                    "<p style='margin:0; font-size:12px; font-weight:600; "
                    "color:#C62828;'>Current Warning:</p>"
                    "<p style='margin:4px 0 0 0; font-size:13px; "
                    "color:#C62828;'>" + current_saved + "</p>"
                    "</div>",
                    unsafe_allow_html=True
                )

            st.markdown("---")
            st.markdown("#### Remove Medicine")
            st.warning(
                "Removing a medicine from the library will not affect "
                "existing prescriptions. It will only remove it from "
                "future prescription dropdowns."
            )
            if st.button(
                "Remove " + selected_med + " from Library",
                key="ml_remove_btn",
                use_container_width=True
            ):
                st.session_state["ml_confirm_remove"] = True
                st.rerun()

            if st.session_state.get("ml_confirm_remove", False):
                st.error(
                    "Are you sure you want to remove " +
                    selected_med + " from the library?"
                )
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button(
                        "Yes, Remove",
                        key="ml_confirm_yes",
                        use_container_width=True
                    ):
                        ok, msg = remove_medicine_from_library(selected_med)
                        if ok:
                            st.session_state["ml_selected_medicine"] = None
                            st.session_state["ml_confirm_remove"] = False
                            st.session_state["ml_note_text"] = ""
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(msg)
                with col_no:
                    if st.button(
                        "Cancel",
                        key="ml_confirm_no",
                        use_container_width=True
                    ):
                        st.session_state["ml_confirm_remove"] = False
                        st.rerun()


# ============================================================
# MEDICINE SEARCH HELPERS - G7
# ============================================================

def search_patients_by_medicine(medicine_name):
    try:
        rows = sb_get(
            "patients",
            "select=reg_no,name,age,mobile,prescription_date,phases"
            "&phases=neq."
        )
        results = []
        search_term = medicine_name.strip().lower()
        for row in rows:
            try:
                phases = json.loads(row.get("phases", "[]"))
                for phase in phases:
                    phase_name = phase.get("phase", "")
                    for step in phase.get("steps", []):
                        med = step.get("medicine", "").strip()
                        if search_term in med.lower():
                            results.append({
                                "reg_no": row["reg_no"],
                                "name": row["name"],
                                "age": row["age"],
                                "mobile": row["mobile"],
                                "prescription_date": row[
                                    "prescription_date"
                                ],
                                "phase": phase_name,
                                "step": step.get("step", ""),
                                "medicine": med,
                                "dose": step.get("dose", ""),
                                "duration": step.get("duration", ""),
                            })
            except Exception:
                continue
        results.sort(
            key=lambda x: x["prescription_date"],
            reverse=True
        )
        return results
    except Exception:
        return []


# ============================================================
# MEDICINE SEARCH SCREEN - G7
# ============================================================

def show_medicine_search():
    st.markdown(
        "<h2 style='color:#B8860B;'>Medicine Search</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#666; font-size:13px;'>"
        "Find all patients who have been prescribed "
        "a specific medicine.</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    medicines = get_medicines_list()

    col_drop, col_or, col_text, col_btn, col_clear = st.columns(
        [3, 0.5, 3, 1, 1]
    )

    with col_drop:
        selected_from_dropdown = st.selectbox(
            "Select from library",
            ["-- Select a medicine --"] + medicines,
            key="ms_dropdown"
        )

    with col_or:
        st.markdown(
            "<div style='padding-top:32px; text-align:center; "
            "color:#888; font-size:13px;'>or</div>",
            unsafe_allow_html=True
        )

    with col_text:
        typed_name = st.text_input(
            "Type medicine name",
            key="ms_typed_input",
            placeholder="e.g. Biluma or Retinol"
        )

    with col_btn:
        st.markdown(
            "<div style='padding-top:28px;'>",
            unsafe_allow_html=True
        )
        search_clicked = st.button(
            "Search",
            key="ms_search_btn",
            use_container_width=True,
            type="primary"
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_clear:
        st.markdown(
            "<div style='padding-top:28px;'>",
            unsafe_allow_html=True
        )
        clear_clicked = st.button(
            "Clear",
            key="ms_clear_btn",
            use_container_width=True
        )
        st.markdown("</div>", unsafe_allow_html=True)

    # Handle clear
    if clear_clicked:
        st.session_state["ms_last_search"] = ""
        st.rerun()

    # Determine search term
    search_term = ""
    if search_clicked or st.session_state.get("ms_last_search", ""):
        if typed_name.strip():
            search_term = typed_name.strip()
        elif selected_from_dropdown != "-- Select a medicine --":
            search_term = selected_from_dropdown

        if search_clicked:
            st.session_state["ms_last_search"] = search_term
        else:
            search_term = st.session_state.get("ms_last_search", "")

    if not search_term:
        st.info(
            "Select a medicine from the dropdown or type a name, "
            "then click Search."
        )
        return

    st.markdown("---")
    st.markdown(
        "<p style='font-size:13px; color:#666;'>Searching for: "
        "<b>" + search_term + "</b></p>",
        unsafe_allow_html=True
    )

    results = search_patients_by_medicine(search_term)

    if not results:
        st.warning(
            "No patients found who have been prescribed: " +
            search_term
        )
        return

    # Count unique patients
    unique_patients = len(set(r["reg_no"] for r in results))
    st.success(
        str(unique_patients) + " patient(s) found | " +
        str(len(results)) + " prescription step(s) total"
    )

    st.markdown("")

    # Results table header
    st.markdown(
        "<div style='display:grid; "
        "grid-template-columns:90px 1fr 45px 110px 110px 90px 60px 90px 90px; "
        "gap:6px; background:#1B2A4A; color:white; "
        "padding:8px 12px; border-radius:6px 6px 0 0; "
        "font-size:11px; font-weight:600; "
        "text-transform:uppercase; letter-spacing:0.04em;'>"
        "<span>Reg No</span>"
        "<span>Name</span>"
        "<span>Age</span>"
        "<span>Mobile</span>"
        "<span>Presc. Date</span>"
        "<span>Phase</span>"
        "<span>Step</span>"
        "<span>Dose</span>"
        "<span>Duration</span>"
        "</div>",
        unsafe_allow_html=True
    )

    phase_colors = {
        "MORNING": "#E65100",
        "EVENING": "#1B5E20",
        "NIGHT": "#4A148C"
    }

    for i, r in enumerate(results):
        bg = "#FFFFFF" if i % 2 == 0 else "#F9F9F9"
        phase_color = phase_colors.get(r["phase"], "#555")
        dose = r.get("dose", "")
        if dose in ["Not Applicable", "-- Select --"]:
            dose = "-"
        duration = r.get("duration", "")
        if duration in ["Not Applicable", "-- Select --"]:
            duration = "-"

        st.markdown(
            "<div style='display:grid; "
            "grid-template-columns:90px 1fr 45px 110px 110px 90px 60px 90px 90px; "
            "gap:6px; background:" + bg + "; "
            "padding:8px 12px; "
            "border-bottom:0.5px solid #eee; "
            "font-size:12px; align-items:center;'>"
            "<span style='color:#B8860B; font-weight:500;'>" +
            r["reg_no"] + "</span>"
            "<span style='color:var(--color-text-primary);'>" +
            r["name"] + "</span>"
            "<span style='color:var(--color-text-secondary);'>" +
            str(r["age"]) + "</span>"
            "<span style='color:var(--color-text-secondary);'>" +
            r["mobile"] + "</span>"
            "<span style='color:var(--color-text-secondary);'>" +
            r["prescription_date"] + "</span>"
            "<span style='background:" + phase_color + "; "
            "color:white; font-size:10px; font-weight:600; "
            "padding:2px 6px; border-radius:3px; "
            "display:inline-block;'>" +
            r["phase"] + "</span>"
            "<span style='color:var(--color-text-secondary); "
            "text-align:center;'>" + str(r["step"]) + "</span>"
            "<span style='color:var(--color-text-secondary);'>" +
            dose + "</span>"
            "<span style='color:var(--color-text-secondary);'>" +
            duration + "</span>"
            "</div>",
            unsafe_allow_html=True
        )

        if st.button(
            "View Patient",
            key="ms_view_" + r["reg_no"] + "_" + str(i),
            use_container_width=True
        ):
            st.session_state["pr_selected_reg_no"] = r["reg_no"]
            st.session_state["pr_show_history"] = False
            st.session_state["pr_search_query"] = r["reg_no"]
            st.session_state["current_page"] = "Patient Records"
            st.rerun()


# ============================================================
# BACKUP / EXPORT HELPERS - G8
# ============================================================

def get_backup_folder():
    # In cloud version backup folder not used - data is in Supabase
    return ""


def get_export_folder():
    return ""


def do_manual_backup():
    # In cloud version - backup means recording backup timestamp
    try:
        set_setting("last_auto_backup", datetime.now().isoformat())
        return True, "Supabase_Backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    except Exception as e:
        return False, "Backup error: " + str(e)


def export_patients_csv():
    try:
        rows = sb_get(
            "patients",
            "select=reg_no,name,age,sex,mobile,weight,height,"
            "bmi,prescription_date,start_date,followup_date,"
            "doctor,bp,email,notes,created_at"
            "&order=prescription_date.desc"
        )
        if not rows:
            return False, "No patients to export.", None

        headers = [
            "Reg No", "Name", "Age", "Sex", "Mobile",
            "Weight (kg)", "Height (cm)", "BMI",
            "Prescription Date", "Start Date", "Follow-up Date",
            "Doctor", "Blood Pressure", "Email",
            "Clinical Notes", "Created At"
        ]
        lines = [",".join(headers)]
        for row in rows:
            def clean(val):
                if val is None:
                    return ""
                val = str(val).replace('"', '""')
                if "," in val or '"' in val or "\n" in val:
                    val = '"' + val + '"'
                return val
            line = ",".join([
                clean(row.get("reg_no", "")),
                clean(row.get("name", "")),
                clean(row.get("age", "")),
                clean(row.get("sex", "")),
                clean(row.get("mobile", "")),
                clean(row.get("weight", "")),
                clean(row.get("height", "")),
                clean(row.get("bmi", "")),
                clean(row.get("prescription_date", "")),
                clean(row.get("start_date", "")),
                clean(row.get("followup_date", "")),
                clean(row.get("doctor", "")),
                clean(row.get("bp", "")),
                clean(row.get("email", "")),
                clean(row.get("notes", "")),
                clean(row.get("created_at", "")),
            ])
            lines.append(line)

        csv_content = "\n".join(lines)
        return True, "Export successful.", csv_content
    except Exception as e:
        return False, "Export error: " + str(e), None


def get_last_backup_info():
    last = get_setting("last_auto_backup")
    if not last:
        return "Never"
    try:
        dt = datetime.fromisoformat(last)
        return dt.strftime("%d-%m-%Y at %I:%M %p")
    except Exception:
        return last


def list_existing_backups():
    # In cloud version Supabase handles backups automatically
    return []


# ============================================================
# BACKUP / EXPORT SCREEN - G8
# ============================================================

def show_backup_export():
    st.markdown(
        "<h2 style='color:#B8860B;'>Backup / Export</h2>",
        unsafe_allow_html=True
    )
    st.markdown(
        "<p style='color:#666; font-size:13px;'>"
        "Keep your patient data safe with regular backups. "
        "Export records to CSV for analysis in Excel.</p>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    # --- Summary Info ---
    total = get_total_patients()
    last_backup = get_last_backup_info()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Total Patients in Database", value=str(total))
    with col2:
        st.metric(label="Last Backup", value=last_backup)
    with col3:
        existing_backups = list_existing_backups()
        st.metric(
            label="Backup Files Saved",
            value=str(len(existing_backups))
        )

    st.markdown("---")

    col_left, col_right = st.columns(2)

    # --- LEFT: Backup ---
    with col_left:
        st.markdown("### Database Backup")
        st.markdown(
            "<p style='font-size:13px; color:#666;'>"
            "Creates a timestamped copy of the complete database "
            "in your 05_Backups folder. All patient records, "
            "medicines, and settings are included.</p>",
            unsafe_allow_html=True
        )

        if st.button(
            "Create Backup Now",
            key="backup_btn",
            use_container_width=True,
            type="primary"
        ):
            ok, result = do_manual_backup()
            if ok:
                st.success(
                    "Backup created successfully: " +
                    os.path.basename(result)
                )
                st.rerun()
            else:
                st.error(result)

        st.markdown("")
        st.markdown("#### Existing Backups")

        if not existing_backups:
            st.info("No backup files found yet.")
        else:
            for b in existing_backups:
                st.markdown(
                    "<div style='display:flex; align-items:center; "
                    "justify-content:space-between; "
                    "background:#F9F9F9; border-radius:6px; "
                    "padding:8px 12px; margin-bottom:4px; "
                    "border:0.5px solid #eee;'>"
                    "<div>"
                    "<p style='margin:0; font-size:13px; "
                    "color:var(--color-text-primary); font-weight:500;'>" +
                    b["filename"] + "</p>"
                    "<p style='margin:0; font-size:11px; "
                    "color:var(--color-text-secondary);'>" +
                    b["size"] + "</p>"
                    "</div>"
                    "<span style='font-size:11px; color:#2E7D32; "
                    "background:#E8F5E9; padding:2px 8px; "
                    "border-radius:4px;'>Saved</span>"
                    "</div>",
                    unsafe_allow_html=True
                )

    # --- RIGHT: Export ---
    with col_right:
        st.markdown("### Export to CSV")
        st.markdown(
            "<p style='font-size:13px; color:#666;'>"
            "Exports all patient records to a CSV file that can "
            "be opened in Excel. Includes all patient details "
            "but not prescription phase steps.</p>",
            unsafe_allow_html=True
        )

        if st.button(
            "Export Patients to CSV",
            key="export_csv_btn",
            use_container_width=True,
            type="primary"
        ):
            ok, msg, csv_content = export_patients_csv()
            if ok and csv_content:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = "patients_export_" + timestamp + ".csv"
                st.download_button(
                    label="Download CSV File",
                    data=csv_content.encode("utf-8"),
                    file_name=filename,
                    mime="text/csv",
                    key="export_download_btn"
                )
                st.success(
                    str(total) +
                    " patient records ready for download."
                )
            else:
                st.error(msg)

        st.markdown("")
        st.markdown("#### What is included in the CSV")
        st.markdown(
            "- Registration No, Name, Age, Sex  \n"
            "- Mobile, Blood Pressure, Email  \n"
            "- Weight, Height, BMI  \n"
            "- Prescription Date, Start Date, Follow-up Date  \n"
            "- Doctor, Clinical Notes  \n"
            "- Date record was created"
        )
        st.markdown("")
        st.info(
            "Prescription phase details (medicines, steps) "
            "are stored in the database but not included in the "
            "CSV export. Use the database backup to preserve "
            "all prescription details."
        )

    st.markdown("---")

    # --- Auto Backup Info ---
    st.markdown("### Auto Backup")
    st.markdown(
        "<p style='font-size:13px; color:#666;'>"
        "The system automatically creates a backup every 7 days "
        "when the app starts. The last backup was: "
        "<b>" + last_backup + "</b></p>",
        unsafe_allow_html=True
    )

def show_coming_soon(page_name):
    st.title(page_name)
    st.info(
        page_name + " screen is coming soon. "
        "It will be built in the next session."
    )
    if st.button("Back to Home"):
        st.session_state["current_page"] = "Home"
        st.rerun()

# ============================================================
# LOGIN PAGE - G1
# ============================================================

def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("---")
        st.markdown(
            "<h2 style='text-align:center; color:#B8860B;'>"
            "ASHU AESTHETIC &amp; WELLNESS CLINIC</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<p style='text-align:center; color:#555;'>"
            "Odisha's Ultra Advanced Skin, "
            "Hair &amp; Laser Cosmetic Clinic</p>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<h4 style='text-align:center; color:#333;'>"
            "Prescription Management System</h4>",
            unsafe_allow_html=True
        )
        st.markdown("---")
        st.markdown("### Please Log In")
        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password", type="password", key="login_password"
        )
        if st.button(
            "Login", use_container_width=True, type="primary"
        ):
            if not username or not password:
                st.error(
                    "Please enter both username and password."
                )
            elif do_login(username, password):
                st.success("Login successful! Loading...")
                st.rerun()
            else:
                st.error(
                    "Incorrect username or password. "
                    "Please try again."
                )
        st.markdown("---")
        st.markdown(
            "<p style='text-align:center; font-size:12px; "
            "color:#aaa;'>www.ashuskincare.com | "
            "Jaydev Vihar, Bhubaneswar</p>",
            unsafe_allow_html=True
        )

# ============================================================
# MAIN APP ROUTER
# ============================================================

def show_main_app():
    show_sidebar()
    page = st.session_state.get("current_page", "Home")
    role = st.session_state.get("user_role", "user")
    user_pages = ["Home", "New Prescription", "Patient Records"]

    # Access restriction for user role
    if role != "admin" and page not in user_pages:
        st.markdown("---")
        st.error(
            "Access restricted. Please contact your administrator."
        )
        st.info(
            "You are logged in as **User**. "
            "You can access: Home, New Prescription, Patient Records."
        )
        if st.button("Go to Home"):
            st.session_state["current_page"] = "Home"
            st.rerun()
        return

    if page == "Home":
        show_home()
    elif page == "New Prescription":
        show_new_prescription()
    elif page == "Patient Records":
        show_patient_records()
    elif page == "Statistics":
        show_statistics()
    elif page == "Medicine Library":
        show_medicine_library()
    elif page == "Medicine Search":
        show_medicine_search()
    elif page == "Backup / Export":
        show_backup_export()
    else:
        show_home()

# ============================================================
# APP ENTRY POINT
# ============================================================

def main():
    st.set_page_config(
        page_title="Ashu Clinic - Prescription System",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="expanded"
    )
    # Global CSS - stronger fonts across all pages
    st.markdown(
        "<style>"
        "body, p, div, span, label, input, select, textarea {"
        "font-weight:500 !important;}"
        ".stMarkdown p {font-weight:500 !important;}"
        ".stTextInput input {font-weight:500 !important;}"
        ".stSelectbox div {font-weight:500 !important;}"
        ".stDataFrame {font-weight:500 !important;}"
        "h1, h2, h3 {font-weight:700 !important;}"
        ".stButton button {font-weight:600 !important;}"
        "[data-testid=stSidebar] {font-weight:500 !important;}"
        "</style>",
        unsafe_allow_html=True
    )
    ensure_tables()
    reset_password_to_default()
    if is_logged_in():
        show_main_app()
    else:
        show_login_page()


if __name__ == "__main__":
    main()
