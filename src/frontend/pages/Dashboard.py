import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from pathlib import Path
import requests
import io
 
st.set_page_config(page_title="Recruiter Panel", page_icon="💼", layout="wide")
 
# Auth Guard
if "recruiter_logged_in" not in st.session_state or not st.session_state["recruiter_logged_in"]:
    st.warning("Please log in to access the recruiter panel.")
    st.switch_page("pages/Recruiter_Login.py")
    st.stop()
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600&display=swap');
 
html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Inter', sans-serif !important;
    background: linear-gradient(145deg, #0A1628 0%, #0F1B2D 45%, #13233A 75%, #0D1F35 100%) !important;
    background-size: 300% 300% !important;
    animation: gradientMove 20s ease infinite !important;
    background-attachment: fixed !important;
}
 
@keyframes gradientMove {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
 
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
 
#MainMenu, footer, header { visibility: hidden; }
 
/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(10, 18, 32, 0.97) !important;
    border-right: 1px solid rgba(0, 201, 167, 0.08) !important;
}
 
/* Nav container */
.nav-container {
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
    background: rgba(22, 34, 54, 0.7);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    padding: 10px;
    border-radius: 16px;
    border: 1px solid rgba(143, 164, 190, 0.1);
}
 
/* Nav buttons */
div[data-testid="stHorizontalBlock"] div.stButton > button {
    background: transparent !important;
    color: #8FA4BE !important;
    border: 1px solid rgba(143, 164, 190, 0.18) !important;
    border-radius: 12px !important;
    padding: 10px 20px !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
    font-family: 'Inter', sans-serif !important;
    letter-spacing: 0.2px !important;
}
div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
    background: rgba(0, 201, 167, 0.07) !important;
    border-color: rgba(0, 201, 167, 0.3) !important;
    color: #00C9A7 !important;
    transform: translateY(-1px) !important;
}
 
/* Section box */
.section-box {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    padding: 38px;
    border-radius: 22px;
    border: 1px solid rgba(143, 164, 190, 0.1);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    margin-bottom: 24px;
    animation: fadeIn 0.7s ease-out;
}
 
/* Metric cards — match app.py custom-card */
.metric-card {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    padding: 26px 22px;
    border-radius: 22px;
    text-align: center;
    border: 1px solid rgba(143, 164, 190, 0.1);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    position: relative;
    overflow: hidden;
}
.metric-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #00C9A7, #FFB547);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.metric-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 32px 70px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 201, 167, 0.25);
    border-color: rgba(0, 201, 167, 0.22);
}
.metric-card:hover::after { opacity: 1; }
 
.metric-title {
    color: #8FA4BE;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
    font-family: 'Inter', sans-serif;
}
.metric-value {
    font-family: 'Outfit', sans-serif;
    color: #E8EDF3;
    font-size: 32px;
    font-weight: 800;
    letter-spacing: -0.5px;
}
 
/* Primary button */
div.stButton > button {
    background: linear-gradient(135deg, #00C9A7 0%, #00A88B 100%) !important;
    color: #0A1628 !important;
    font-weight: 700 !important;
    padding: 13px 24px !important;
    border-radius: 12px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 6px 22px rgba(0, 201, 167, 0.28) !important;
    font-size: 15px !important;
    letter-spacing: 0.2px !important;
    font-family: 'Inter', sans-serif !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #00DFBB 0%, #00C9A7 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 32px rgba(0, 201, 167, 0.42) !important;
}
div.stButton > button:active { transform: translateY(0) !important; }
 
/* Sidebar logout button */
[data-testid="stSidebar"] div.stButton > button {
    background: rgba(255, 107, 107, 0.08) !important;
    color: #FF6B6B !important;
    border: 1px solid rgba(255, 107, 107, 0.22) !important;
    box-shadow: none !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] div.stButton > button:hover {
    background: rgba(255, 107, 107, 0.15) !important;
    border-color: rgba(255, 107, 107, 0.4) !important;
    transform: none !important;
    box-shadow: none !important;
}
 
/* Download button */
div.stDownloadButton > button {
    background: rgba(0, 201, 167, 0.08) !important;
    color: #00C9A7 !important;
    border: 1px solid rgba(0, 201, 167, 0.25) !important;
    box-shadow: none !important;
    font-weight: 600 !important;
}
div.stDownloadButton > button:hover {
    background: rgba(0, 201, 167, 0.15) !important;
    box-shadow: none !important;
    transform: none !important;
}
 
/* Selectbox */
div[data-testid="stSelectbox"] > div > div {
    background: rgba(22, 34, 54, 0.8) !important;
    border-color: rgba(143, 164, 190, 0.2) !important;
    color: #E8EDF3 !important;
    border-radius: 12px !important;
}
 
/* Progress bar */
div[data-testid="stProgress"] > div {
    background: rgba(22, 34, 54, 0.8) !important;
    border-radius: 8px !important;
}
div[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, #00C9A7, #FFB547) !important;
    border-radius: 8px !important;
}
 
/* Dataframe */
div[data-testid="stDataFrame"] {
    border-radius: 14px !important;
    overflow: hidden !important;
    border: 1px solid rgba(143, 164, 190, 0.1) !important;
}
 
/* Text overrides */
p, span, [data-testid="stMarkdownContainer"] p { color: #C8D8E8; }
strong { color: #E8EDF3 !important; }
h3, h4 { color: #E8EDF3 !important; font-family: 'Outfit', sans-serif !important; }
 
div[data-testid="stAlert"] { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)
 
# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.markdown("""
    <div style='text-align:center; margin-bottom:20px; padding-top:8px;'>
        <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='76'
             style='border-radius:50%; border:2px solid #00C9A7; box-shadow:0 4px 18px rgba(0,201,167,0.25);'>
        <h4 style='font-family:Outfit,sans-serif; color:#E8EDF3; margin-top:12px; margin-bottom:2px; font-weight:800; font-size:16px;'>HR Admin</h4>
        <p style='color:#8FA4BE; font-size:12px; margin:0;'>Admissions Team</p>
    </div>
""", unsafe_allow_html=True)
 
if st.sidebar.button("Log Out 🚪", use_container_width=True):
    st.session_state["recruiter_logged_in"] = False
    st.switch_page("pages/Recruiter_Login.py")
    st.stop()
 
# -----------------------------
# Navigation State
# -----------------------------
if "active_page" not in st.session_state:
    st.session_state.active_page = "dashboard"
 
def set_page(page):
    st.session_state.active_page = page
 
# -----------------------------
# Header + Nav
# -----------------------------
st.markdown("""
    <div style='margin-bottom:6px; animation: fadeIn 0.8s ease-out;'>
        <h2 style='font-family:Outfit,sans-serif; font-weight:900; color:#E8EDF3; font-size:2rem; letter-spacing:-0.5px; margin-bottom:4px;'>
            Welcome back, <span style='color:#00C9A7;'>Admin</span> 👋
        </h2>
        <p style='color:#8FA4BE; font-size:15px; margin:0;'>Access candidate reports and manage interview results easily.</p>
    </div>
""", unsafe_allow_html=True)
 
st.markdown('<div class="nav-container">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Dashboard 📊", key="nav_dashboard"):
        set_page("dashboard")
with col2:
    if st.button("Candidates 👥", key="nav_candidates"):
        set_page("candidates")
with col3:
    if st.button("Reports 📄", key="nav_reports"):
        set_page("reports")
st.markdown('</div>', unsafe_allow_html=True)
 
# -----------------------------
# LOAD DATA
# -----------------------------
st.markdown('<div class="section-box">', unsafe_allow_html=True)
 
API_URL = "http://localhost:8000/api"
df = pd.DataFrame(columns=["id", "name", "email", "position", "status", "score"])
 
try:
    response = requests.get(f"{API_URL}/candidates")
    if response.status_code == 200:
        candidates_data = response.json()["candidates"]
        if candidates_data:
            df = pd.DataFrame(candidates_data)
            if "position" not in df.columns:
                df["position"] = "Agentic AI"
            if "score" not in df.columns:
                df["score"] = 0.0
            if "status" not in df.columns:
                df["status"] = "Pending"
    else:
        st.error("Failed to load candidate data from backend API.")
except Exception as e:
    st.error(f"Error connecting to backend API: {e}")
    st.info("Please make sure the backend uvicorn server is running on http://localhost:8000")
    st.stop()
 
def clean_for_pdf(text: str) -> str:
    cleaned = ""
    for char in str(text):
        if ord(char) < 256:
            cleaned += char
        else:
            if char == "—": cleaned += "-"
            elif char in ["\u201c", "\u201d"]: cleaned += '"'
            elif char in ["\u2018", "\u2019"]: cleaned += "'"
            else: cleaned += "?"
    return cleaned
 
# -----------------------------
# DASHBOARD PAGE
# -----------------------------
if st.session_state.active_page == "dashboard":
    st.markdown("""
        <h2 style='font-family:Outfit,sans-serif; font-weight:900; font-size:2rem; color:#E8EDF3; margin-bottom:4px; letter-spacing:-0.5px;'>
            📊 Dashboard Overview
        </h2>
        <p style='color:#8FA4BE; margin-bottom:36px; font-size:15px;'>
            Real-time insights into candidate performance and interview progress.
        </p>
    """, unsafe_allow_html=True)
 
    if df.empty:
        st.warning("No candidate records found. Once candidates begin interviews, their metrics will appear here.")
    else:
        completed = len(df[df["status"].str.lower().str.strip().isin(["completed", "accepted", "rejected", "interviewed"])])
        pending = len(df[df["status"].str.lower().str.strip().isin(["pending", "interviewing", "in_progress"])])
        avg_score = round(df["score"].mean(), 2)
 
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Candidates</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Completed</div><div class='metric-value'>{completed}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Pending / Active</div><div class='metric-value'>{pending}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Average Score</div><div class='metric-value'>{avg_score}%</div></div>", unsafe_allow_html=True)
 
        st.markdown("<br><hr style='border-color:rgba(143,164,190,0.1);'><br>", unsafe_allow_html=True)
 
        colA, colB = st.columns(2)
        with colA:
            st.markdown("<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif; margin-bottom:12px;'>Status Distribution</h4>", unsafe_allow_html=True)
            color_discrete_map = {}
            for stat in df["status"].unique():
                s_lower = stat.lower().strip()
                if s_lower in ["completed", "accepted", "interviewed"]:
                    color_discrete_map[stat] = "#00C9A7"
                elif s_lower == "rejected":
                    color_discrete_map[stat] = "#FF6B6B"
                else:
                    color_discrete_map[stat] = "#FFB547"
            fig1 = px.pie(df, names="status", color="status", color_discrete_map=color_discrete_map)
            fig1.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#C8D8E8")
            st.plotly_chart(fig1, use_container_width=True)
 
        with colB:
            st.markdown("<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif; margin-bottom:12px;'>Candidate Scores</h4>", unsafe_allow_html=True)
            fig2 = px.bar(df, x="name", y="score", color="score", color_continuous_scale=["#162236", "#00C9A7"])
            fig2.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#C8D8E8")
            st.plotly_chart(fig2, use_container_width=True)
 
        st.markdown("<br><hr style='border-color:rgba(143,164,190,0.1);'><br>", unsafe_allow_html=True)
 
        st.markdown("<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif; margin-bottom:12px;'>Interview Progress Trend</h4>", unsafe_allow_html=True)
        df_line = df.copy()
        df_line["index"] = range(1, len(df_line) + 1)
        fig3 = px.line(df_line, x="index", y="score", markers=True, color_discrete_sequence=["#00C9A7"])
        fig3.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#C8D8E8")
        st.plotly_chart(fig3, use_container_width=True)
 
# -----------------------------
# CANDIDATES PAGE
# -----------------------------
elif st.session_state.active_page == "candidates":
    st.markdown("""
        <h2 style='font-family:Outfit,sans-serif; font-weight:900; font-size:2rem; color:#E8EDF3; margin-bottom:4px; letter-spacing:-0.5px;'>
            👥 Candidates Overview
        </h2>
        <p style='color:#8FA4BE; margin-bottom:36px; font-size:15px;'>
            All candidate records at a glance.
        </p>
    """, unsafe_allow_html=True)
 
    if df.empty:
        st.warning("No candidate records found.")
    else:
        completed = len(df[df["status"].str.lower().str.strip().isin(["completed", "accepted", "rejected", "interviewed"])])
        pending = len(df[df["status"].str.lower().str.strip().isin(["pending", "interviewing", "in_progress"])])
        avg_score = round(df["score"].mean(), 2)
 
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Candidates</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Completed</div><div class='metric-value'>{completed}</div></div>", unsafe_allow_html=True)
        with col3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Pending / Active</div><div class='metric-value'>{pending}</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Average Score</div><div class='metric-value'>{avg_score}%</div></div>", unsafe_allow_html=True)
 
        st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:28px 0;'>", unsafe_allow_html=True)
 
        st.markdown("<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif; margin-bottom:12px;'>📋 Candidates Table</h4>", unsafe_allow_html=True)
        st.dataframe(df, use_container_width=True, height=400)
 
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Candidates')
        excel_bytes = buffer.getvalue()
 
        st.download_button(
            label="📥 Export Candidates List to Excel",
            data=excel_bytes,
            file_name="candidates_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
 
        st.markdown("<h4 style='color:#FFB547; font-weight:800; font-family:Outfit,sans-serif; margin-top:36px; margin-bottom:12px;'>🏆 Top Candidates</h4>", unsafe_allow_html=True)
        top3 = df.sort_values(by="score", ascending=False).head(3)
        st.dataframe(top3, use_container_width=True)
 
# -----------------------------
# REPORTS PAGE
# -----------------------------
elif st.session_state.active_page == "reports":
    st.markdown("""
        <h2 style='font-family:Outfit,sans-serif; font-weight:900; font-size:2rem; color:#E8EDF3; margin-bottom:4px; letter-spacing:-0.5px;'>
            📄 Candidate Reports
        </h2>
        <p style='color:#8FA4BE; margin-bottom:28px; font-size:15px;'>
            Generate and download individual candidate assessment reports.
        </p>
    """, unsafe_allow_html=True)
 
    if df.empty:
        st.warning("No candidate records available to generate reports.")
    else:
        candidate_names = df["name"].tolist()
        candidate = st.selectbox("Select Candidate", candidate_names)
 
        if candidate:
            row = df[df["name"] == candidate].iloc[0]
            email = row["email"]
            position = row["position"]
            status = row["status"]
            score_value = row["score"]
            progress_score = score_value / 100
 
            st.markdown(f"""
                <h4 style='font-family:Outfit,sans-serif; color:#E8EDF3; font-weight:800; margin-top:24px; margin-bottom:16px;'>
                    👤 {candidate}
                </h4>
            """, unsafe_allow_html=True)
 
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                st.markdown(f"**📧 Email:** `{email}`")
                st.markdown(f"**💼 Position:** {position}")
            with col2:
                st.metric("Status", status)
                st.metric("Score", f"{score_value}%")
            with col3:
                if score_value >= 85:
                    analysis = "Excellent performance. Strong alignment with bootcamp goals."
                    st.success("Excellent ✨")
                elif score_value >= 70:
                    analysis = "Good performance. Competent skills, ready to grow."
                    st.info("Very Good 👍")
                else:
                    analysis = "Needs improvement. Recommend additional prep."
                    st.warning("Needs Improvement ⚠️")
 
            st.progress(progress_score)
            st.caption(f"**Admissions Summary:** {analysis}")
            st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:20px 0;'>", unsafe_allow_html=True)
 
            # PDF Generator
            class PDF(FPDF):
                def header(self):
                    self.set_fill_color(10, 22, 40)
                    self.rect(0, 0, 210, 30, 'F')
                    self.set_font("Arial", "B", 16)
                    self.set_text_color(255, 255, 255)
                    self.cell(0, 10, "CANDIDATE ASSESSMENT REPORT", align="C", ln=True)
                    self.ln(10)
 
                def footer(self):
                    self.set_y(-15)
                    self.set_font("Arial", "I", 8)
                    self.set_text_color(128, 128, 128)
                    self.cell(0, 10, f"Page {self.page_no()}", align="C")
 
            def generate_pdf():
                pdf = PDF()
                pdf.add_page()
                pdf.ln(15)
                pdf.set_draw_color(220, 220, 220)
                pdf.rect(10, 40, 190, 100)
                pdf.set_text_color(50, 50, 50)
 
                def add_info(label, value):
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(40, 10, f"{clean_for_pdf(label)}:", ln=False)
                    pdf.set_font("Arial", "", 11)
                    pdf.cell(0, 10, clean_for_pdf(value), ln=True)
                    pdf.set_draw_color(240, 240, 240)
                    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
 
                pdf.ln(2)
                add_info("Full Name", candidate)
                add_info("Email", email)
                add_info("Position", position)
                add_info("Status", status)
                add_info("Final Score", f"{score_value}%")
 
                pdf.ln(10)
                pdf.set_font("Arial", "B", 12)
                pdf.set_text_color(0, 201, 167)
                pdf.cell(0, 10, "Evaluation & Analysis", ln=True)
 
                pdf.set_fill_color(245, 247, 250)
                pdf.set_text_color(60, 60, 60)
                pdf.set_font("Arial", "I", 11)
                pdf.multi_cell(0, 12, clean_for_pdf(f"Result: {analysis}\nThis report is automatically generated on {pd.Timestamp.now().strftime('%Y-%m-%d')}."), border=1, fill=True)
 
                return pdf.output(dest="S").encode("latin-1")
 
            try:
                pdf_data = generate_pdf()
                st.download_button(
                    "📄 Download Professional PDF Report",
                    data=pdf_data,
                    file_name=f"{candidate.replace(' ', '_')}_Assessment_Report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as pdf_err:
                st.error(f"Error generating PDF report: {pdf_err}")
 
st.markdown('</div>', unsafe_allow_html=True)