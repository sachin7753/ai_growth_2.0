# ------------------- IMPORTS -------------------
import pandas as pd
import numpy as np
import re
import torch
import torch.nn as nn
import streamlit as st
import joblib
import json
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import matplotlib.pyplot as plt
import smtplib
from email.message import EmailMessage
import requests
import os
from datetime import datetime

# ------------------- PAGE CONFIG -------------------
st.set_page_config(page_title="Child Growth Advisor", page_icon="🧒", layout="wide")

# ------------------- CONFIG & CONSTANTS -------------------
HFA_BOYS_FILE = "tab_hfa_boys_p_0_5.xlsx"
HFA_GIRLS_FILE = "tab_hfa_girls_p_0_5.xlsx"
WFH_BOYS_FILE = "tab_wfh_boys_p_0_5.xlsx"
WFH_GIRLS_FILE = "tab_wfh_girls_p_0_5.xlsx"
MODEL_PATH = "growth_model.pth"
SCALER_PATH = "scaler.joblib"
PARAMS_PATH = "best_params.json"
DAYS_PER_MONTH = 30.4375
CLASS_LABELS = {0: "Underweight", 1: "Healthy", 2: "Overweight", 3: "Obese", 4: "Stunted", 5: "Normal Ht"}

# ------------------- AI MODEL -------------------
class GrowthNet(nn.Module):
    def __init__(self, n_layers=2, n_units=64, dropout_rate=0.3):
        super().__init__()
        layers = []
        in_features = 4
        for i in range(n_layers):
            layers.append(nn.Linear(in_features, n_units))
            layers.append(nn.ReLU())
            layers.append(nn.Dropout(dropout_rate))
            in_features = n_units
        layers.append(nn.Linear(in_features, len(CLASS_LABELS)))
        self.model = nn.Sequential(*layers)
    def forward(self, x):
        return self.model(x)

# ------------------- LOAD MODEL & SCALER -------------------
@st.cache_resource
def load_model_and_scaler(model_path: str, scaler_path: str, params_path: str):
    try:
        with open(params_path, 'r') as f:
            best_params = json.load(f)
        model = GrowthNet(n_layers=best_params['n_layers'], n_units=best_params['n_units'], dropout_rate=best_params['dropout_rate'])
        model.load_state_dict(torch.load(model_path))
        model.eval()
        scaler = joblib.load(scaler_path)
        return model, scaler
    except FileNotFoundError as e:
        st.error(f"Required file not found: {e}. Please run train.py first.")
        return None, None

@st.cache_data
def load_ref(path: str, primary_col_regex: str):
    try:
        df = pd.read_excel(path)
        primary_col = next((c for c in df.columns if re.search(primary_col_regex, str(c), re.I)), None)
        if not primary_col:
            raise ValueError(f"No primary column found in {path}")
        pcols = [c for c in df.columns if re.match(r"P\d+", str(c))]
        df = df[[primary_col] + pcols].copy()
        df.columns = ["primary"] + pcols
        return df, pcols
    except FileNotFoundError:
        st.error(f"Dataset file not found: '{path}'")
        return None, None

# ------------------- CORE CALCULATION -------------------
def interp_curve(ref_df, pcols, val):
    values = ref_df.iloc[:, 0].values.astype(float)
    if val <= values.min():
        row = ref_df.iloc[0]
    elif val >= values.max():
        row = ref_df.iloc[-1]
    else:
        idx = np.searchsorted(values, val, side="right")
        v0, v1 = values[idx - 1], values[idx]
        frac = (val - v0) / (v1 - v0)
        row0, row1 = ref_df.iloc[idx - 1], ref_df.iloc[idx]
        return {float(re.findall(r"\d+", c)[0]): row0[c] + frac * (row1[c] - row0[c]) for c in pcols}
    return {float(re.findall(r"\d+", c)[0]): float(row[c]) for c in pcols}

def est_percentile(value, curve):
    pts = sorted(curve.items(), key=lambda item: item[1])
    values = [v for p, v in pts]
    percs = [p for p, v in pts]
    if value <= values[0]:
        return percs[0]
    if value >= values[-1]:
        return percs[-1]
    j = np.searchsorted(values, value, side="right")
    v0, v1, p0, p1 = values[j - 1], values[j], percs[j - 1], percs[j]
    return p0 + (value - v0) / (v1 - v0) * (p1 - p0)

def ai_predict(model, scaler, age_m, ht, wt, sex, wfh_p, hfa_p):
    input_data = np.array([[age_m, ht, wt, 1 if sex == "M" else 0]])
    input_scaled = scaler.transform(input_data)
    x = torch.tensor(input_scaled, dtype=torch.float32)
    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1)
        confidence, pred_idx_tensor = torch.max(probs, dim=1)
        pred_idx = pred_idx_tensor.item()
        confidence_score = confidence.item()
    status = CLASS_LABELS.get(pred_idx, "Unknown")
    bmi = wt / ((ht / 100) ** 2)
    if wfh_p < 3:
        status = "Underweight"
    elif wfh_p > 85:
        status = "Obese" if bmi >= 30 else "Overweight"
    elif bmi >= 30:
        status = "Obese"
    elif bmi >= 25:
        status = "Overweight"
    elif hfa_p < 3 and status in ["Healthy", "Normal Ht"]:
        status = "Stunted"
    elif status == "Underweight" and wfh_p >= 5 and hfa_p < 5:
        status = "Stunted"
    return status, confidence_score

# ------------------- AI RECOMMENDATIONS -------------------
def get_ai_recommendations(status, age_m, wfh_p, hfa_p, bmi):
    recs = [f"**Status: {status}** (BMI: {bmi:.1f} | Wt-for-Ht: P{wfh_p:.1f})"]
    if status in ["Obese", "Overweight"]:
        recs += [
            "- Balanced meals with vegetables, fruits, lean proteins.",
            "- Avoid sugary drinks & high-calorie snacks.",
            "- 60 mins daily physical activity.",
            "- Pediatric consultation if BMI>30 or rapid gain.",
        ]
    elif status == "Underweight":
        recs += [
            "- Increase nutrient-dense foods (nuts, dairy, eggs).",
            "- Frequent small meals.",
            "- Monitor growth monthly.",
        ]
    elif status == "Stunted":
        recs += [
            "- Focus on iron, zinc, vitamin A-rich foods.",
            "- Ensure adequate protein.",
            "- Pediatric evaluation for supplements.",
        ]
    else:
        recs += [
            "- Continue balanced diet & regular meals.",
            "- Encourage 60+ mins active play.",
            "- Regular pediatric check-ups.",
        ]
    return recs

# ------------------- REPORT GENERATION -------------------
def generate_report(age_m, ht, wt, sex, model, scaler):
    hfa_ref, hfa_pcols = load_ref(HFA_BOYS_FILE if sex == "M" else HFA_GIRLS_FILE, r"age|day|month")
    wfh_ref, wfh_pcols = load_ref(WFH_BOYS_FILE if sex == "M" else WFH_GIRLS_FILE, r"height|length")
    if hfa_ref is None or wfh_ref is None:
        return None
    age_d = age_m * DAYS_PER_MONTH
    hfa_curve = interp_curve(hfa_ref, hfa_pcols, age_d)
    hfa_p = est_percentile(ht, hfa_curve)
    wfh_curve = interp_curve(wfh_ref, wfh_pcols, ht)
    wfh_p = est_percentile(wt, wfh_curve)
    ai_status, confidence = ai_predict(model, scaler, age_m, ht, wt, sex, wfh_p, hfa_p)
    bmi = wt / ((ht / 100) ** 2)
    who_msgs = []
    if wfh_p < 3:
        who_msgs.append((f"Wasting risk (P{wfh_p:.1f})", colors.red))
    elif wfh_p > 85:
        who_msgs.append((f"Overweight risk (P{wfh_p:.1f})", colors.red))
    else:
        who_msgs.append(("Wt-for-height healthy.", colors.green))
    if hfa_p < 3:
        who_msgs.append((f"Stunting risk (P{hfa_p:.1f})", colors.red))
    else:
        who_msgs.append(("Ht-for-age healthy.", colors.green))
    recommendations = get_ai_recommendations(ai_status, age_m, wfh_p, hfa_p, bmi)
    return {
        "wfh_p": wfh_p,
        "hfa_p": hfa_p,
        "bmi": bmi,
        "who_msgs": who_msgs,
        "recommendations": recommendations,
        "ai_status": ai_status,
        "confidence": confidence,
        "hfa_curve": hfa_curve,
        "wfh_curve": wfh_curve,
        "age_d": age_d,
        "ht": ht,
        "wt": wt,
    }

# ------------------- PDF REPORT -------------------
def create_pdf_report(child_name, age_months, report):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(3 * cm, height - 3 * cm, f"Child Growth Report: {child_name}")
    c.setFont("Helvetica", 12)
    c.drawString(3 * cm, height - 4 * cm, f"Age: {int(age_months)//12}y {int(age_months)%12}m")
    c.drawString(3 * cm, height - 4.7 * cm, f"Height Percentile: P{report['hfa_p']:.1f}")
    c.drawString(3 * cm, height - 5.4 * cm, f"Weight-for-Height Percentile: P{report['wfh_p']:.1f}")
    c.drawString(3 * cm, height - 6.1 * cm, f"BMI: {report['bmi']:.1f}")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(3 * cm, height - 7 * cm, "WHO Assessment:")
    c.setFont("Helvetica", 12)
    y = height - 7.7 * cm
    for msg, color in report["who_msgs"]:
        c.setFillColor(color)
        c.drawString(4 * cm, y, msg)
        y -= 0.7 * cm
    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", 14)
    c.drawString(3 * cm, y - 0.3 * cm, "AI Recommendations:")
    c.setFont("Helvetica", 12)
    y -= 1 * cm
    for rec in report["recommendations"]:
        c.drawString(4 * cm, y, rec.replace("**", ""))
        y -= 0.7 * cm
        if y < 5 * cm:
            c.showPage()
            y = height - 3 * cm

    hfa_buf = BytesIO()
    wfh_buf = BytesIO()
    plt.figure(figsize=(6, 4))
    plt.plot(list(report["hfa_curve"].keys()), list(report["hfa_curve"].values()), label="Height-for-age", color="green")
    plt.scatter([report["ht"]], [report["ht"]], color="blue", label="Child Height")
    plt.xlabel("Percentile")
    plt.ylabel("Height (cm)")
    plt.title("Height-for-Age Percentile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(hfa_buf, format="PNG")
    plt.close()
    hfa_buf.seek(0)

    plt.figure(figsize=(6, 4))
    plt.plot(list(report["wfh_curve"].keys()), list(report["wfh_curve"].values()), label="Weight-for-height", color="orange")
    plt.scatter([report["ht"]], [report["wt"]], color="red", label="Child Weight")
    plt.xlabel("Percentile")
    plt.ylabel("Weight (kg)")
    plt.title("Weight-for-Height Percentile")
    plt.legend()
    plt.tight_layout()
    plt.savefig(wfh_buf, format="PNG")
    plt.close()
    wfh_buf.seek(0)

    c.showPage()
    c.drawImage(ImageReader(hfa_buf), 2 * cm, height / 2, width=16 * cm, height=9 * cm)
    c.drawImage(ImageReader(wfh_buf), 2 * cm, 2 * cm, width=16 * cm, height=9 * cm)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# ------------------- UPLOAD TO WIX -------------------
def upload_to_wix_media(pdf_buffer, child_name):
    """
    Upload a PDF to the Wix Media Manager so it's available on the Wix site
    without any manual steps.
    Returns the public download URL on success, or None on failure.
    """
    try:
        api_key = st.secrets["wix"]["api_key"]
        site_id = st.secrets["wix"]["site_id"]
    except Exception:
        st.error("Wix credentials not found. Add [wix] section to .streamlit/secrets.toml")
        return None

    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = child_name.replace(" ", "_")
    file_name = f"{safe_name}_Growth_Report_{timestamp}.pdf"

    # Step 1: Generate an upload URL from Wix Media Manager
    gen_url = "https://www.wixapis.com/site-media/v1/files/generate-upload-url"
    payload = {
        "mimeType": "application/pdf",
        "fileName": file_name,
    }

    try:
        resp = requests.post(gen_url, json=payload, headers=headers, timeout=30)
    except requests.RequestException as e:
        st.error(f"Network error contacting Wix: {e}")
        return None

    if resp.status_code != 200:
        st.error(f"Wix generate-upload-url failed ({resp.status_code}): {resp.text}")
        return None

    data = resp.json()
    upload_url = data.get("uploadUrl")

    if not upload_url:
        st.error(f"No uploadUrl in Wix response: {data}")
        return None

    # Step 2: Upload the PDF binary via multipart POST (Wix expected format)
    pdf_buffer.seek(0)

    try:
        upload_resp = requests.post(
            upload_url,
            files={"file": (file_name, pdf_buffer, "application/pdf")},
            timeout=60,
        )
    except requests.RequestException as e:
        st.error(f"Upload to Wix failed: {e}")
        return None

    if upload_resp.status_code not in (200, 201):
        st.error(f"Upload to Wix failed ({upload_resp.status_code}): {upload_resp.text}")
        return None

    # Step 3: Parse the uploaded file info
    try:
        result = upload_resp.json()
    except Exception:
        result = {}

    # Extract the public URL from various possible response shapes
    file_url = None
    if isinstance(result, dict):
        # Try nested paths
        file_info = result.get("file", result)
        file_url = (
            file_info.get("url")
            or file_info.get("fileUrl")
            or file_info.get("originalFileUrl")
        )
        # If we got a Wix media URI like "wix:document://...", build a real URL
        if not file_url:
            file_id = file_info.get("id") or file_info.get("fileId")
            if file_id:
                file_url = f"https://static.wixstatic.com/media/{file_id}"

    if file_url:
        st.success(f"PDF uploaded to Wix Media Manager!")
        st.markdown(f"**Wix Media URL:** [{file_name}]({file_url})")
    else:
        st.warning("PDF was sent to Wix but the public URL could not be determined. "
                   "Check your Wix Media Manager dashboard.")
        st.json(result)

    # Reset buffer for other uses
    pdf_buffer.seek(0)
    return file_url


# ------------------- SAVE TO WIX COLLECTION -------------------
def save_to_wix_collection(child_name, child_id, file_url, roll_number=""):
    """
    Insert a record into the 'ChildReports' CMS collection so the report
    is accessible from the Wix site's CMS (no manual steps).
    """
    try:
        api_key = st.secrets["wix"]["api_key"]
        site_id = st.secrets["wix"]["site_id"]
    except Exception:
        st.error("Wix credentials not found in secrets.")
        return False

    headers = {
        "Authorization": api_key,
        "wix-site-id": site_id,
        "Content-Type": "application/json",
    }

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    title = f"{child_name} Growth Report"
    if roll_number:
        title = f"[{roll_number}] {title}"
    title += f" - {timestamp}"

    data_fields = {
        "title": title,
        "childId": child_id,
        "reportFileUrl": file_url,
    }
    if roll_number:
        data_fields["rollNumber"] = roll_number

    payload = {
        "dataCollectionId": "ChildReports",
        "dataItem": {
            "data": data_fields
        }
    }

    try:
        resp = requests.post(
            "https://www.wixapis.com/wix-data/v2/items",
            json=payload,
            headers=headers,
            timeout=30,
        )
    except requests.RequestException as e:
        st.error(f"Failed to save to Wix collection: {e}")
        return False

    if resp.status_code == 200:
        st.success("Report saved to Wix CMS collection 'ChildReports'!")
        return True
    else:
        st.error(f"Failed to save to collection ({resp.status_code}): {resp.text}")
        return False


# ------------------- SEND EMAIL -------------------
def send_email_report(to_email, pdf_buffer, child_name):
    try:
        user = st.secrets["email"]["user"]
        app_password = st.secrets["email"]["app_password"]
        msg = EmailMessage()
        msg["Subject"] = f"{child_name} Growth Report"
        msg["From"] = user
        msg["To"] = to_email
        msg.set_content(f"Hello,\n\nPlease find attached the growth report for {child_name}.")
        pdf_buffer.seek(0)
        msg.add_attachment(pdf_buffer.read(), maintype="application", subtype="pdf", filename=f"{child_name}_Growth_Report.pdf")
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(user, app_password)
            smtp.send_message(msg)
        st.success(f"Email sent successfully to {to_email}!")
    except Exception as e:
        st.error(f"Failed to send email: {type(e).__name__} - {e}")

# ------------------- STREAMLIT INTERFACE -------------------
st.title("🧒 Hybrid AI Child Growth Advisor with PDF Charts & Email")
growth_model, scaler = load_model_and_scaler(MODEL_PATH, SCALER_PATH, PARAMS_PATH)

with st.sidebar:
    st.header("Child Info & Measurements")
    child_name = st.text_input("Child's Name", value="John Doe")
    sex_options = {"Male": "M", "Female": "F"}
    sex_label = st.radio("Sex", options=sex_options.keys(), horizontal=True)
    sex = sex_options[sex_label]

    # ✅ Age input in years, internally converted to months
    age_years = st.number_input("Age (in Years)", min_value=0.0, max_value=5.0, value=2.0, step=0.1)
    age_months = int(age_years * 12)

    height_cm = st.number_input("Height (cm)", 40.0, 130.0, value=85.0, step=0.1)
    weight_kg = st.number_input("Weight (kg)", 1.0, 40.0, value=12.0, step=0.1)
    roll_number = st.text_input("Roll Number", value="", help="Child's roll number for easy report lookup")
    child_id = st.text_input("Child ID", value="", help="Unique ID to link this report to a child in Wix CMS")
    parent_email = st.text_input("Parent's Email", value="example@gmail.com")
    generate_button = st.button("Generate & Send Report")

if generate_button and growth_model and scaler:
    with st.spinner("Analyzing and generating report..."):
        report = generate_report(int(age_months), float(height_cm), float(weight_kg), sex, growth_model, scaler)
    if report:
        st.header("Growth Report Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Age", f"{int(age_months)//12}y {int(age_months)%12}m")
        col2.metric("Height Pctl", f"P{report['hfa_p']:.1f}")
        col3.metric("Wt/Ht Pctl", f"P{report['wfh_p']:.1f}")
        col4.metric("BMI", f"{report['bmi']:.1f}")
        st.markdown("---")
        col_who, col_ai = st.columns(2)
        with col_who:
            st.subheader("📈 WHO Assessment")
            for msg, color in report["who_msgs"]:
                st.markdown(f"- {msg}")
        with col_ai:
            st.subheader("🤖 AI Recommendations")
            st.caption(f"Status: **{report['ai_status']}** | Confidence: **{report['confidence']:.1%}**")
            for tip in report["recommendations"]:
                st.markdown(f"- {tip}")
        pdf_buffer = create_pdf_report(child_name, int(age_months), report)
        st.download_button("📄 Download PDF", data=pdf_buffer, file_name=f"{child_name}_Growth_Report.pdf", mime="application/pdf")

        # --- Upload PDF to Wix automatically ---
        st.markdown("---")
        st.subheader("☁️ Wix Upload")
        with st.spinner("Uploading PDF to Wix Media Manager..."):
            wix_url = upload_to_wix_media(pdf_buffer, child_name)

        # --- Save to Wix CMS Collection ---
        if wix_url:
            with st.spinner("Saving to Wix CMS collection..."):
                cid = child_id if child_id else child_name.replace(' ', '_').lower()
                rn = roll_number if roll_number else ""
                save_to_wix_collection(child_name, cid, wix_url, rn)

        if parent_email:
            send_email_report(parent_email, pdf_buffer, child_name)
elif not (growth_model and scaler):
    st.warning("Cannot generate report because AI model or scaler is not loaded.")
