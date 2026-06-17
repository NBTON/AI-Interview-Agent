import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path
import requests
import io
import os
from xml.sax.saxutils import escape as xml_escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Flowable

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

API_URL = os.environ.get("API_URL", "http://localhost:8000/api").rstrip("/")
df = pd.DataFrame(columns=["id", "name", "email", "position", "status", "score", "report_id", "session_id", "recommendation"])
dashboard_stats = {}

def api_get(path: str):
    response = requests.get(f"{API_URL}{path}", timeout=20)
    if response.status_code == 503:
        st.error("Live recruiter analytics require Supabase configuration. No sample recruiter data is available.")
        st.stop()
    if response.status_code != 200:
        detail = response.text
        try:
            detail = response.json().get("detail", detail)
        except Exception:
            pass
        raise RuntimeError(detail)
    return response.json()

try:
    dashboard_stats = api_get("/recruiter/dashboard")
    candidates_data = api_get("/recruiter/candidates")
    if candidates_data:
        df = pd.DataFrame(candidates_data)
        df = df.rename(columns={"bootcamp": "position"})
        if "position" not in df.columns:
            df["position"] = "Agentic AI"
        if "score" not in df.columns:
            df["score"] = 0.0
        df["score"] = pd.to_numeric(df["score"], errors="coerce").fillna(0.0)
        if "status" not in df.columns:
            df["status"] = "new"
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

def escape_for_paragraph(text: str) -> str:
    return xml_escape(clean_for_pdf(text))

PDF_NAVY = colors.HexColor("#0A1628")
PDF_INK = colors.HexColor("#172033")
PDF_MUTED = colors.HexColor("#667085")
PDF_TEAL = colors.HexColor("#00A88B")
PDF_GOLD = colors.HexColor("#FFB547")
PDF_RED = colors.HexColor("#D92D20")
PDF_BLUE = colors.HexColor("#2E90FA")
PDF_LIGHT = colors.HexColor("#F4F7FB")
PDF_BORDER = colors.HexColor("#D8E2EF")


class ScoreGauge(Flowable):
    def __init__(self, score_percent: float, width: float = 1.65 * inch, height: float = 1.15 * inch):
        super().__init__()
        self.score_percent = max(0, min(float(score_percent or 0), 100))
        self.width = width
        self.height = height

    def draw(self):
        canvas = self.canv
        radius = 34
        center_x = self.width / 2
        center_y = 38
        canvas.setLineWidth(9)
        canvas.setStrokeColor(colors.HexColor("#DDE7F3"))
        canvas.arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, 180, -180)
        canvas.setStrokeColor(PDF_TEAL if self.score_percent >= 70 else PDF_GOLD if self.score_percent >= 50 else PDF_RED)
        canvas.arc(center_x - radius, center_y - radius, center_x + radius, center_y + radius, 180, -180 * (self.score_percent / 100))
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 18)
        canvas.drawCentredString(center_x, center_y - 3, f"{self.score_percent:.0f}%")
        canvas.setFillColor(colors.HexColor("#D6E3F0"))
        canvas.setFont("Helvetica", 7)
        canvas.drawCentredString(center_x, 9, "overall score")


class TopicBar(Flowable):
    def __init__(self, label: str, score_percent: float, width: float = 4.6 * inch, height: float = 0.28 * inch):
        super().__init__()
        self.label = clean_for_pdf(label).title()
        self.score_percent = max(0, min(float(score_percent or 0), 100))
        self.width = width
        self.height = height

    def draw(self):
        canvas = self.canv
        label_width = 1.15 * inch
        bar_x = label_width
        bar_w = self.width - label_width - 0.45 * inch
        fill_w = bar_w * (self.score_percent / 100)
        color = PDF_TEAL if self.score_percent >= 70 else PDF_GOLD if self.score_percent >= 50 else PDF_RED
        canvas.setFillColor(PDF_INK)
        canvas.setFont("Helvetica-Bold", 7.5)
        canvas.drawString(0, 3, self.label[:18])
        canvas.setFillColor(colors.HexColor("#E9EEF5"))
        canvas.roundRect(bar_x, 2, bar_w, 7, 3, fill=1, stroke=0)
        canvas.setFillColor(color)
        canvas.roundRect(bar_x, 2, max(fill_w, 3), 7, 3, fill=1, stroke=0)
        canvas.setFillColor(PDF_MUTED)
        canvas.setFont("Helvetica-Bold", 7)
        canvas.drawRightString(self.width, 2, f"{self.score_percent:.0f}%")


def draw_pdf_page(canvas, doc):
    canvas.saveState()
    page_width, page_height = letter
    canvas.setFillColor(PDF_NAVY)
    canvas.rect(0, page_height - 0.36 * inch, page_width, 0.36 * inch, fill=1, stroke=0)
    canvas.setFillColor(PDF_TEAL)
    canvas.rect(0, page_height - 0.39 * inch, page_width, 0.03 * inch, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(0.6 * inch, page_height - 0.23 * inch, "AI Interview Agent - Candidate Evaluation")
    canvas.setFillColor(PDF_MUTED)
    canvas.setFont("Helvetica", 7)
    canvas.drawRightString(page_width - 0.6 * inch, 0.32 * inch, f"Page {doc.page}")
    canvas.restoreState()

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
        completed = dashboard_stats.get("completed_interviews", len(df[df["status"].str.lower().str.strip().isin(["completed", "accepted", "rejected", "interviewed"])]))
        pending = dashboard_stats.get("pending_interviews", 0) + dashboard_stats.get("in_progress_interviews", 0)
        avg_score = dashboard_stats.get("average_score", round(df["score"].mean(), 2))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Candidates</div><div class='metric-value'>{dashboard_stats.get('total_candidates', len(df))}</div></div>", unsafe_allow_html=True)
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
            Review live final evaluations, turn-by-turn evidence, and full interview chat logs.
        </p>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No candidate records available to generate reports.")
    else:
        candidate_options = {
            f"{row['name']} - {row.get('email', 'no email')}": row["id"]
            for _, row in df.sort_values("name").iterrows()
        }
        selected_label = st.selectbox("Select Candidate", list(candidate_options.keys()))

        if selected_label:
            candidate_id = candidate_options[selected_label]
            try:
                bundle = api_get(f"/recruiter/candidates/{candidate_id}")
            except Exception as exc:
                st.error(f"Unable to load candidate report: {exc}")
                st.stop()

            candidate_data = bundle.get("candidate") or {}
            report = bundle.get("report") or {}
            session = bundle.get("session") or {}
            profile = bundle.get("profile") or {}
            turns = bundle.get("turns") or []
            messages = bundle.get("messages") or []

            name = candidate_data.get("name", "Unknown candidate")
            email = candidate_data.get("email", "")
            position = candidate_data.get("bootcamp", "Agentic AI")
            status = candidate_data.get("status", "new")
            score_value = float(candidate_data.get("score") or 0)
            progress_score = min(max(score_value / 100, 0), 1)
            recommendation = (report.get("recommendation") or candidate_data.get("recommendation") or "pending").upper()

            st.markdown(f"""
                <h4 style='font-family:Outfit,sans-serif; color:#E8EDF3; font-weight:800; margin-top:24px; margin-bottom:16px;'>
                    👤 {name}
                </h4>
            """, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            with col1:
                st.markdown(f"**📧 Email:** `{email or 'Not recorded'}`")
                st.markdown(f"**💼 Program:** {position}")
                st.markdown(f"**Session:** `{session.get('id', candidate_data.get('session_id') or 'No session')}`")
            with col2:
                st.metric("Status", status)
            with col3:
                st.metric("Score", f"{score_value:.1f}%")
            with col4:
                st.metric("Decision", recommendation)

            st.progress(progress_score)
            st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:20px 0;'>", unsafe_allow_html=True)

            if not report:
                st.warning("No final interview report exists yet for this candidate.")
            else:
                st.markdown("### Final Evaluation")
                st.markdown(f"**Summary:** {report.get('summary') or 'Not recorded.'}")

                s_col, w_col = st.columns(2)
                with s_col:
                    st.markdown("#### Specific Strengths")
                    st.info(report.get("strengths") or "Not recorded.")
                with w_col:
                    st.markdown("#### Specific Weaknesses")
                    st.warning(report.get("weaknesses") or "Not recorded.")

                st.markdown("#### Decision Notes")
                st.write(report.get("decision_notes") or "Not recorded.")

                topic_scores = report.get("topic_scores") or {}
                if isinstance(topic_scores, dict) and topic_scores.get("topic_scores"):
                    score_rows = []
                    for topic, info in topic_scores["topic_scores"].items():
                        if isinstance(info, dict):
                            score_rows.append({
                                "topic": topic,
                                "score": round(float(info.get("final_topic_score") or 0) * 20, 1),
                                "turns": len(info.get("turn_scores") or []),
                            })
                    if score_rows:
                        st.markdown("#### Topic Scores")
                        st.dataframe(pd.DataFrame(score_rows), use_container_width=True, hide_index=True)

            st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:24px 0;'>", unsafe_allow_html=True)
            st.markdown("### Question-by-Question History")
            if not turns:
                st.info("No evaluated interview turns were recorded for this candidate.")
            else:
                for turn in turns:
                    turn_title = f"Turn {turn.get('turn_number')} - {str(turn.get('topic') or 'topic').title()} - Score {turn.get('score', 'N/A')}/5"
                    with st.expander(turn_title, expanded=False):
                        st.markdown("**Question**")
                        st.write(turn.get("question") or "Not recorded.")
                        st.markdown("**Candidate Answer**")
                        st.write(turn.get("answer") or "No answer recorded.")
                        st.markdown("**Evaluator Feedback**")
                        st.write(turn.get("feedback") or "No feedback recorded.")
                        st.markdown(f"**Needs Probe:** {'Yes' if turn.get('needs_probe') else 'No'}")
                        extracted_skills = turn.get("extracted_skills") or []
                        extracted_info = turn.get("extracted_info") or {}
                        if extracted_skills:
                            st.markdown("**Extracted Skills**")
                            st.write(", ".join(map(str, extracted_skills)))
                        if extracted_info:
                            st.markdown("**Extracted Info**")
                            st.json(extracted_info)

            st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:24px 0;'>", unsafe_allow_html=True)
            profile_tab, chat_tab = st.tabs(["Candidate Profile", "Full Chat Log"])
            with profile_tab:
                if profile:
                    profile_view = {
                        "background": profile.get("background"),
                        "education": profile.get("education"),
                        "experience": profile.get("experience"),
                        "skills": profile.get("skills"),
                        "projects": profile.get("projects"),
                    }
                    st.json(profile_view)
                else:
                    st.info("No structured profile has been recorded for this candidate.")
            with chat_tab:
                if messages:
                    for message in messages:
                        role = str(message.get("role") or "message").title()
                        created = message.get("created_at") or ""
                        st.markdown(f"**{role}** `{created}`")
                        st.write(message.get("content") or "")
                        st.markdown("---")
                else:
                    st.info("No chat messages were recorded for this session.")

            def generate_reportlab_pdf() -> bytes:
                def make_topic_rows() -> list[dict]:
                    rows = []
                    score_payload = report.get("topic_scores") or {}
                    if isinstance(score_payload, dict) and score_payload.get("topic_scores"):
                        for topic, info in score_payload["topic_scores"].items():
                            if isinstance(info, dict):
                                rows.append({
                                    "topic": topic,
                                    "score": round(float(info.get("final_topic_score") or 0) * 20, 1),
                                    "turns": len(info.get("turn_scores") or []),
                                })
                    if not rows:
                        seen_topics = {}
                        for turn in turns:
                            topic = str(turn.get("topic") or "General")
                            try:
                                turn_score = float(turn.get("score") or 0) * 20
                            except (TypeError, ValueError):
                                turn_score = 0
                            seen_topics.setdefault(topic, []).append(turn_score)
                        rows = [
                            {"topic": topic, "score": round(sum(scores) / len(scores), 1), "turns": len(scores)}
                            for topic, scores in seen_topics.items()
                            if scores
                        ]
                    return rows

                topic_rows = make_topic_rows()
                decision_color = {
                    "ACCEPT": PDF_TEAL,
                    "REVIEW": PDF_GOLD,
                    "REJECT": PDF_RED,
                }.get(recommendation, PDF_BLUE)

                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=letter,
                    rightMargin=0.55 * inch,
                    leftMargin=0.55 * inch,
                    topMargin=0.62 * inch,
                    bottomMargin=0.55 * inch,
                )
                styles = getSampleStyleSheet()
                styles["Title"].fontName = "Helvetica-Bold"
                styles["Title"].fontSize = 22
                styles["Title"].leading = 26
                styles["Title"].textColor = PDF_NAVY
                styles["Heading2"].fontName = "Helvetica-Bold"
                styles["Heading2"].fontSize = 13
                styles["Heading2"].leading = 16
                styles["Heading2"].textColor = PDF_NAVY
                styles["Heading3"].fontName = "Helvetica-Bold"
                styles["Heading3"].fontSize = 10
                styles["Heading3"].leading = 12
                styles["Heading3"].textColor = PDF_INK
                styles["BodyText"].fontSize = 9
                styles["BodyText"].leading = 12.5
                styles["BodyText"].textColor = PDF_INK
                styles.add(ParagraphStyle(name="SmallBody", parent=styles["BodyText"], fontSize=8, leading=10.5, textColor=PDF_MUTED))
                styles.add(ParagraphStyle(name="WhiteTitle", parent=styles["Title"], fontSize=20, leading=24, textColor=colors.white))
                styles.add(ParagraphStyle(name="WhiteSmall", parent=styles["SmallBody"], textColor=colors.HexColor("#D6E3F0")))
                styles.add(ParagraphStyle(name="CalloutTitle", parent=styles["Heading3"], textColor=PDF_TEAL))

                hero = Table(
                    [[
                        [
                            Paragraph("Candidate Evaluation Snapshot", styles["WhiteTitle"]),
                            Paragraph(f"Generated on {pd.Timestamp.now().strftime('%Y-%m-%d')}", styles["WhiteSmall"]),
                        ],
                        ScoreGauge(score_value),
                    ]],
                    colWidths=[4.65 * inch, 1.6 * inch],
                )
                hero.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), PDF_NAVY),
                    ("BOX", (0, 0), (-1, -1), 0, PDF_NAVY),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 18),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 16),
                    ("TOPPADDING", (0, 0), (-1, -1), 16),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                ]))

                summary_table = Table(
                    [
                        ["Candidate", clean_for_pdf(name), "Decision", recommendation],
                        ["Email", clean_for_pdf(email or "Not recorded"), "Status", clean_for_pdf(status).title()],
                        ["Program", clean_for_pdf(position), "Session", clean_for_pdf(session.get("id", candidate_data.get("session_id") or "No session"))],
                    ],
                    colWidths=[0.8 * inch, 2.65 * inch, 0.75 * inch, 2.05 * inch],
                )
                summary_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                    ("BOX", (0, 0), (-1, -1), 0.8, PDF_BORDER),
                    ("LINEBELOW", (0, 0), (-1, 1), 0.35, PDF_BORDER),
                    ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                    ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                    ("TEXTCOLOR", (0, 0), (0, -1), PDF_MUTED),
                    ("TEXTCOLOR", (2, 0), (2, -1), PDF_MUTED),
                    ("TEXTCOLOR", (3, 0), (3, 0), decision_color),
                    ("FONTNAME", (3, 0), (3, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 7),
                ]))

                kpi_table = Table(
                    [[
                        Paragraph(f"<b>{score_value:.1f}%</b><br/><font color='#667085'>Overall Score</font>", styles["BodyText"]),
                        Paragraph(f"<b>{recommendation}</b><br/><font color='#667085'>Recommendation</font>", styles["BodyText"]),
                        Paragraph(f"<b>{len(turns)}</b><br/><font color='#667085'>Evaluated Turns</font>", styles["BodyText"]),
                    ]],
                    colWidths=[2.05 * inch, 2.05 * inch, 2.05 * inch],
                )
                kpi_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), PDF_LIGHT),
                    ("BOX", (0, 0), (-1, -1), 0.8, PDF_BORDER),
                    ("LINEBEFORE", (1, 0), (-1, -1), 0.5, PDF_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ]))

                story = [hero, Spacer(1, 0.16 * inch), summary_table, Spacer(1, 0.12 * inch), kpi_table, Spacer(1, 0.22 * inch)]

                if topic_rows:
                    topic_visuals = [[TopicBar(row["topic"], row["score"])] for row in topic_rows[:8]]
                    topic_table = Table(topic_visuals, colWidths=[4.8 * inch])
                    topic_table.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.white),
                        ("BOX", (0, 0), (-1, -1), 0.8, PDF_BORDER),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]))
                    story.extend([
                        Paragraph("Topic Score Profile", styles["Heading2"]),
                        Spacer(1, 0.05 * inch),
                        topic_table,
                        Spacer(1, 0.18 * inch),
                    ])

                callout_table = Table(
                    [[
                        [Paragraph("Strengths", styles["CalloutTitle"]), Paragraph(escape_for_paragraph(report.get("strengths") or "Not recorded."), styles["SmallBody"])],
                        [Paragraph("Risks / Gaps", styles["Heading3"]), Paragraph(escape_for_paragraph(report.get("weaknesses") or "Not recorded."), styles["SmallBody"])],
                    ]],
                    colWidths=[3.05 * inch, 3.05 * inch],
                )
                callout_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (0, 0), colors.HexColor("#ECFDF3")),
                    ("BACKGROUND", (1, 0), (1, 0), colors.HexColor("#FFF7E6")),
                    ("BOX", (0, 0), (-1, -1), 0.8, PDF_BORDER),
                    ("LINEBEFORE", (1, 0), (1, 0), 0.5, PDF_BORDER),
                    ("PADDING", (0, 0), (-1, -1), 10),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]))

                story = [
                    *story,
                    Paragraph("Final Evaluation", styles["Heading2"]),
                    Paragraph(escape_for_paragraph(report.get("summary") or "No final summary recorded."), styles["BodyText"]),
                    Spacer(1, 0.09 * inch),
                    callout_table,
                    Spacer(1, 0.12 * inch),
                    Paragraph("Decision Notes", styles["Heading3"]),
                    Paragraph(escape_for_paragraph(report.get("decision_notes") or "Not recorded."), styles["BodyText"]),
                    Spacer(1, 0.2 * inch),
                    Paragraph("Question History", styles["Heading2"]),
                ]

                for turn in turns:
                    try:
                        turn_score = float(turn.get("score") or 0) * 20
                    except (TypeError, ValueError):
                        turn_score = 0
                    score_color = PDF_TEAL if turn_score >= 70 else PDF_GOLD if turn_score >= 50 else PDF_RED
                    turn_header = Table(
                        [[
                            Paragraph(escape_for_paragraph(f"Turn {turn.get('turn_number')} - {str(turn.get('topic') or 'General').title()}"), styles["Heading3"]),
                            Paragraph(escape_for_paragraph(f"{turn.get('score', 'N/A')}/5"), styles["Heading3"]),
                        ]],
                        colWidths=[5.2 * inch, 0.8 * inch],
                    )
                    turn_header.setStyle(TableStyle([
                        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF6FF")),
                        ("BOX", (0, 0), (-1, -1), 0.5, PDF_BORDER),
                        ("TEXTCOLOR", (1, 0), (1, 0), score_color),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("PADDING", (0, 0), (-1, -1), 6),
                    ]))
                    story.extend([
                        turn_header,
                        Paragraph(escape_for_paragraph(f"Question: {turn.get('question') or 'Not recorded.'}"), styles["SmallBody"]),
                        Paragraph(escape_for_paragraph(f"Answer: {turn.get('answer') or 'Not recorded.'}"), styles["SmallBody"]),
                        Paragraph(escape_for_paragraph(f"Feedback: {turn.get('feedback') or 'Not recorded.'}"), styles["SmallBody"]),
                        Spacer(1, 0.09 * inch),
                    ])

                doc.build(story, onFirstPage=draw_pdf_page, onLaterPages=draw_pdf_page)
                return buffer.getvalue()

            try:
                st.download_button(
                    "📄 Download Evaluation Snapshot PDF",
                    data=generate_reportlab_pdf(),
                    file_name=f"{name.replace(' ', '_')}_evaluation_snapshot.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    disabled=not report,
                )
            except Exception as pdf_err:
                st.error(f"Error generating PDF report: {pdf_err}")

st.markdown('</div>', unsafe_allow_html=True)
