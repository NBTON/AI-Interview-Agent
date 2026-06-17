import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import requests
import io
import matplotlib.pyplot as plt
import tempfile

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

/* Chat bubble styles */
.chat-bubble-q {
    background: rgba(0, 201, 167, 0.08);
    border: 1px solid rgba(0, 201, 167, 0.2);
    border-radius: 14px 14px 14px 4px;
    padding: 14px 18px;
    margin-bottom: 10px;
    color: #C8D8E8;
    font-size: 14px;
    line-height: 1.6;
}
.chat-bubble-a {
    background: rgba(22, 34, 54, 0.9);
    border: 1px solid rgba(143, 164, 190, 0.15);
    border-radius: 14px 14px 4px 14px;
    padding: 14px 18px;
    margin-bottom: 16px;
    color: #E8EDF3;
    font-size: 14px;
    line-height: 1.6;
    margin-left: 24px;
}
.chat-label-q {
    font-size: 11px;
    font-weight: 700;
    color: #00C9A7;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
    font-family: 'Inter', sans-serif;
}
.chat-label-a {
    font-size: 11px;
    font-weight: 700;
    color: #8FA4BE;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 6px;
    font-family: 'Inter', sans-serif;
    margin-left: 24px;
}
.turn-score-badge {
    display: inline-block;
    background: rgba(0, 201, 167, 0.12);
    border: 1px solid rgba(0, 201, 167, 0.3);
    color: #00C9A7;
    font-size: 11px;
    font-weight: 700;
    padding: 3px 10px;
    border-radius: 20px;
    margin-left: 10px;
    vertical-align: middle;
}
.turn-header {
    display: flex;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(143, 164, 190, 0.08);
}
.turn-number {
    font-family: 'Outfit', sans-serif;
    font-size: 13px;
    font-weight: 800;
    color: #FFB547;
    background: rgba(255, 181, 71, 0.1);
    border: 1px solid rgba(255, 181, 71, 0.2);
    padding: 3px 10px;
    border-radius: 8px;
    margin-right: 10px;
}
.topic-tag {
    font-size: 11px;
    font-weight: 600;
    color: #8FA4BE;
    background: rgba(143, 164, 190, 0.08);
    border: 1px solid rgba(143, 164, 190, 0.15);
    padding: 3px 10px;
    border-radius: 20px;
}
.strength-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    background: rgba(0, 201, 167, 0.06);
    border: 1px solid rgba(0, 201, 167, 0.15);
    border-radius: 10px;
    margin-bottom: 8px;
    color: #C8D8E8;
    font-size: 14px;
}
.weakness-item {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 14px;
    background: rgba(255, 107, 107, 0.06);
    border: 1px solid rgba(255, 107, 107, 0.15);
    border-radius: 10px;
    margin-bottom: 8px;
    color: #C8D8E8;
    font-size: 14px;
}
.decision-box {
    background: rgba(22, 34, 54, 0.9);
    border: 1px solid rgba(0, 201, 167, 0.2);
    border-left: 4px solid #00C9A7;
    border-radius: 12px;
    padding: 20px 24px;
    color: #C8D8E8;
    font-size: 14px;
    line-height: 1.7;
    font-style: italic;
}

/* Metric cards */
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
# LOAD LIVE DATA FROM /api/candidates
# -----------------------------
st.markdown('<div class="section-box">', unsafe_allow_html=True)

API_URL = "http://localhost:8000/api"
df = pd.DataFrame(columns=["id", "name", "email", "position", "status", "score"])

try:
    response = requests.get(f"{API_URL}/candidates")
    if response.status_code == 200:
        candidates_data = response.json().get("candidates", [])
        if candidates_data:
            df = pd.DataFrame(candidates_data)
            if "position" not in df.columns:
                df["position"] = "Agentic AI"
            if "score" not in df.columns:
                df["score"] = 0.0
            if "status" not in df.columns:
                df["status"] = "Pending"
        else:
            st.warning("No candidates returned from the API yet.")
    else:
        st.error(f"Failed to load candidate data. Server responded with status {response.status_code}.")
except Exception as e:
    st.error(f"Error connecting to backend API: {e}")
    st.info("Please make sure the backend uvicorn server is running on http://localhost:8000")
    st.stop()

# -----------------------------
# HELPER: fetch live session data for a candidate
# -----------------------------
def fetch_session(candidate_id):
    """Fetch full interview session from /api/interview/session/{id}. Returns dict or None."""
    try:
        res = requests.get(f"{API_URL}/interview/session/{candidate_id}", timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return None

# -----------------------------
# HELPER: clean text for PDF latin-1 encoding
# -----------------------------
def clean_for_pdf(text: str) -> str:
    cleaned = ""
    for char in str(text):
        if ord(char) < 256:
            cleaned += char
        else:
            if char == "—":
                cleaned += "-"
            elif char in ["\u201c", "\u201d"]:
                cleaned += '"'
            elif char in ["\u2018", "\u2019"]:
                cleaned += "'"
            else:
                cleaned += "?"
    return cleaned

# ============================
# DASHBOARD PAGE
# ============================
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
        pending = len(df[df["status"].str.lower().str.strip().isin(["pending", "new", "not started"])])
        in_progress = len(df[df["status"].str.lower().str.strip().isin(["in progress", "interviewing", "in_progress"])])
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

# ============================
# CANDIDATES PAGE
# ============================
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
        pending = len(df[df["status"].str.lower().str.strip().isin(["pending", "new", "not started"])])
        in_progress = len(df[df["status"].str.lower().str.strip().isin(["in progress", "interviewing", "in_progress"])])
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
        st.dataframe(df, use_container_width=True, height=300)

        buffer = io.BytesIO()
        try:
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
        except Exception as excel_err:
            st.error(f"Excel Export Error: {excel_err}")

        st.markdown("<h4 style='color:#FFB547; font-weight:800; font-family:Outfit,sans-serif; margin-top:36px; margin-bottom:12px;'>🏆 Top Candidates</h4>", unsafe_allow_html=True)
        top3 = df.sort_values(by="score", ascending=False).head(3)
        st.dataframe(top3, use_container_width=True)

# ============================
# REPORTS PAGE — Live deep-dive wired to /api/interview/session/{id}
# ============================
elif st.session_state.active_page == "reports":
    st.markdown("""
        <h2 style='font-family:Outfit,sans-serif; font-weight:900; font-size:2rem; color:#E8EDF3; margin-bottom:4px; letter-spacing:-0.5px;'>
            Document Candidate Reports &amp; Deep-Dive
        </h2>
        <p style='color:#8FA4BE; margin-bottom:28px; font-size:15px;'>
            Review complete candidate overview and download the full custom executive assessment snapshot.
        </p>
    """, unsafe_allow_html=True)

    if df is None or df.empty:
        st.warning("⚠️ No candidate records available to generate reports.")
    else:
        candidate_names = df["name"].tolist()
        candidate = st.selectbox("Select Candidate", candidate_names)

        if candidate:
            row = df[df["name"] == candidate].iloc[0]
            candidate_id = row.get("id")
            email = row.get("email", "N/A")
            position = row.get("position", "N/A")
            status = str(row.get("status", "")).lower().strip()
            raw_score = row.get("score")

            st.markdown(
                f"<h3 style='font-family:Outfit,sans-serif; color:#E8EDF3; font-weight:800;"
                f" margin-top:24px; margin-bottom:16px;'>👤 {candidate}</h3>",
                unsafe_allow_html=True,
            )

            # ── Guard: not started / no score ──────────────────────────────
            if (
                status in ["not started", "pending", "none", ""]
                or raw_score is None
                or (isinstance(raw_score, float) and pd.isna(raw_score))
            ):
                st.markdown(f"""
                    <div style="background-color: #1F2A38; border-left: 5px solid #FFB547;
                                padding: 20px; border-radius: 8px;">
                        <h4 style="color: #FFB547; margin: 0 0 8px 0; font-weight: 700;">
                            ⏳ Evaluation Not Available
                        </h4>
                        <p style="color: #8FA4BE; margin: 0; font-size: 14px;">
                            This candidate <strong>has not started</strong> or hasn't finished the
                            interview session yet. The automated scoring, agent deep-dive comments,
                            and PDF download button will appear immediately once the status updates
                            to <strong>'Completed'</strong>.
                        </p>
                    </div>
                """, unsafe_allow_html=True)

            # ── Completed candidate: full deep-dive ────────────────────────
            else:
                score_value = float(raw_score)

                # ── Fetch live session data ──────────────────────────────────
                session_data = fetch_session(candidate_id) or {}

                ai_analysis   = session_data.get("ai_analysis",
                                  session_data.get("summary",
                                    "No final analysis compiled by Decision Support Agent yet."))
                decision_notes = session_data.get("decision_notes",
                                   session_data.get("notes",
                                     "Candidate evaluation is based on technical ability, "
                                     "communication skills, and problem-solving performance."))
                turns_data     = session_data.get("turns", [])

                strengths_list  = session_data.get("strengths", [])
                weaknesses_list = session_data.get("weaknesses", [])

                if isinstance(strengths_list, str):
                    strengths_list = [s.strip() for s in strengths_list.split(",") if s.strip()]
                if isinstance(weaknesses_list, str):
                    weaknesses_list = [w.strip() for w in weaknesses_list.split(",") if w.strip()]

                # ── Quick-stats bar ──────────────────────────────────────────
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**📧 Email:** `{email}`")
                    st.markdown(f"**💼 Position:** {position}")
                    st.progress(min(max(score_value / 100.0, 0.0), 1.0))
                with col2:
                    st.metric("Final Score", f"{int(score_value)}%")
                    if score_value >= 80:
                        st.success("Accepted ✨")
                    elif score_value >= 60:
                        st.info("Interviewed 👍")
                    else:
                        st.warning("Needs Review ⚠️")

                st.markdown("<br>", unsafe_allow_html=True)

                # ============================================================
                # DEEP-DIVE SECTION — Question-by-Question Chat Log
                # ============================================================
                if turns_data:
                    st.markdown(
                        "<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif;"
                        " margin-bottom:18px;'>💬 Full Interview Chat Log</h4>",
                        unsafe_allow_html=True,
                    )

                    for i, turn in enumerate(turns_data, start=1):
                        question    = turn.get("question", turn.get("agent_message", "—"))
                        answer      = turn.get("answer",   turn.get("candidate_message", "—"))
                        topic       = turn.get("topic", "")
                        turn_score  = turn.get("score")
                        turn_feedback = turn.get("feedback", turn.get("comment", ""))

                        score_badge = ""
                        if turn_score is not None:
                            score_badge = (
                                f"<span class='turn-score-badge'>"
                                f"Score: {turn_score}/5</span>"
                            )
                        topic_tag = (
                            f"<span class='topic-tag'>{topic}</span>" if topic else ""
                        )

                        st.markdown(f"""
                            <div style='margin-bottom:20px;'>
                                <div class='turn-header'>
                                    <span class='turn-number'>Q{i}</span>
                                    {topic_tag}
                                    {score_badge}
                                </div>
                                <div class='chat-label-q'>Interviewer</div>
                                <div class='chat-bubble-q'>{question}</div>
                                <div class='chat-label-a'>Candidate</div>
                                <div class='chat-bubble-a'>{answer}</div>
                                {"<div style='color:#8FA4BE; font-size:12px; font-style:italic; margin-left:24px; margin-bottom:4px;'>💡 " + str(turn_feedback) + "</div>" if turn_feedback else ""}
                            </div>
                        """, unsafe_allow_html=True)

                    st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:28px 0;'>", unsafe_allow_html=True)
                else:
                    st.markdown(
                        "<p style='color:#8FA4BE; font-style:italic;'>"
                        "No turn-by-turn conversation data available for this session.</p>",
                        unsafe_allow_html=True,
                    )

                # ============================================================
                # STRENGTHS & WEAKNESSES
                # ============================================================
                sw_col1, sw_col2 = st.columns(2)

                with sw_col1:
                    st.markdown(
                        "<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif;"
                        " margin-bottom:14px;'>✅ Strengths</h4>",
                        unsafe_allow_html=True,
                    )
                    if strengths_list:
                        for s in strengths_list:
                            st.markdown(
                                f"<div class='strength-item'>"
                                f"<span style='color:#00C9A7; font-size:16px;'>●</span>"
                                f" {s}</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            "<p style='color:#8FA4BE; font-style:italic; font-size:13px;'>"
                            "No specific strengths logged by the agent yet.</p>",
                            unsafe_allow_html=True,
                        )

                with sw_col2:
                    st.markdown(
                        "<h4 style='color:#FF6B6B; font-weight:800; font-family:Outfit,sans-serif;"
                        " margin-bottom:14px;'>⚠️ Weaknesses</h4>",
                        unsafe_allow_html=True,
                    )
                    if weaknesses_list:
                        for w in weaknesses_list:
                            st.markdown(
                                f"<div class='weakness-item'>"
                                f"<span style='color:#FF6B6B; font-size:16px;'>●</span>"
                                f" {w}</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown(
                            "<p style='color:#8FA4BE; font-style:italic; font-size:13px;'>"
                            "No critical weaknesses identified.</p>",
                            unsafe_allow_html=True,
                        )

                st.markdown("<hr style='border-color:rgba(143,164,190,0.1); margin:28px 0;'>", unsafe_allow_html=True)

                # ============================================================
                # AI SUMMARY
                # ============================================================
                st.markdown(
                    "<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif;"
                    " margin-bottom:14px;'>🤖 AI Interview Summary</h4>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div style='background:rgba(22,34,54,0.8); border:1px solid rgba(143,164,190,0.15);"
                    f" border-radius:14px; padding:20px 24px; color:#C8D8E8; font-size:14px; line-height:1.8;'>"
                    f"{ai_analysis}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                # ============================================================
                # DECISION NOTES
                # ============================================================
                st.markdown(
                    "<h4 style='color:#00C9A7; font-weight:800; font-family:Outfit,sans-serif;"
                    " margin-bottom:14px;'>📝 Decision Notes</h4>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f"<div class='decision-box'>{decision_notes}</div>",
                    unsafe_allow_html=True,
                )

                st.markdown("<br>", unsafe_allow_html=True)

                # ============================================================
                # PDF GENERATION — unchanged logic, uses live session_data
                # ============================================================
                class PDF(FPDF):
                    def header(self):
                        self.set_fill_color(10, 22, 40)
                        self.rect(0, 0, 210, 25, "F")
                        self.set_font("Arial", "B", 14)
                        self.set_text_color(255, 255, 255)
                        self.set_y(5)
                        self.cell(0, 8, "CANDIDATE ASSESSMENT REPORT", ln=True, align="C")
                        self.set_font("Arial", "", 9)
                        self.cell(0, 5, "AI Interview Evaluation System", ln=True, align="C")
                        self.set_y(35)

                    def footer(self):
                        self.set_y(-12)
                        self.set_font("Arial", "I", 8)
                        self.set_text_color(150, 150, 150)
                        self.cell(0, 10, f"Page {self.page_no()}", align="C")

                def generate_pdf():
                    pdf = PDF()
                    pdf.add_page()
                    pdf.set_auto_page_break(auto=True, margin=15)

                    # 1. Candidate Information
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 201, 167)
                    pdf.cell(0, 8, "Candidate Information", ln=True)
                    pdf.ln(2)

                    pdf.set_font("Arial", "B", 10)
                    pdf.set_text_color(255, 255, 255)
                    pdf.set_fill_color(15, 32, 55)
                    pdf.cell(45, 8, "Name", border=1, align="C", fill=True)
                    pdf.cell(60, 8, "Email", border=1, align="C", fill=True)
                    pdf.cell(45, 8, "Position", border=1, align="C", fill=True)
                    pdf.cell(40, 8, "Status", border=1, align="C", fill=True)
                    pdf.ln()

                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(30, 30, 30)
                    pdf.set_fill_color(245, 247, 250)
                    pdf.cell(45, 8, clean_for_pdf(candidate), border=1, align="C", fill=True)
                    pdf.cell(60, 8, clean_for_pdf(email), border=1, align="C", fill=True)
                    pdf.cell(45, 8, clean_for_pdf(position), border=1, align="C", fill=True)
                    pdf.cell(40, 8, clean_for_pdf(status.title()), border=1, align="C", fill=True)
                    pdf.ln(10)

                    # 2. Final Evaluation
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 201, 167)
                    pdf.cell(0, 8, "Final Evaluation", ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(40, 40, 40)
                    decision       = "Excellent Match" if score_value >= 85 else "Needs Improvement" if score_value < 60 else "Passed Screen"
                    recommendation = "Highly Recommended" if score_value >= 85 else "Not Recommended" if score_value < 60 else "Recommended"
                    pdf.cell(0, 6, f"Score: {round(score_value, 2)}%", ln=True)
                    pdf.cell(0, 6, f"Decision: {decision}", ln=True)
                    pdf.cell(0, 6, f"Recommendation: {recommendation}", ln=True)
                    pdf.ln(6)

                    # 3. Interview Summary
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 201, 167)
                    pdf.cell(0, 8, "Interview Summary", ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(40, 40, 40)
                    pdf.multi_cell(0, 6, clean_for_pdf(ai_analysis))
                    pdf.ln(6)

                    # 4. Question-by-Question Log
                    if turns_data:
                        pdf.set_font("Arial", "B", 12)
                        pdf.set_text_color(0, 201, 167)
                        pdf.cell(0, 8, "Interview Transcript", ln=True)
                        pdf.ln(2)
                        for idx, turn in enumerate(turns_data, start=1):
                            q_text = turn.get("question", turn.get("agent_message", ""))
                            a_text = turn.get("answer",   turn.get("candidate_message", ""))
                            t_topic = turn.get("topic", "")
                            t_score = turn.get("score")
                            t_feedback = turn.get("feedback", turn.get("comment", ""))

                            score_str = f"  [Score: {t_score}/5]" if t_score is not None else ""
                            topic_str = f"  [{t_topic}]" if t_topic else ""

                            pdf.set_font("Arial", "B", 10)
                            pdf.set_text_color(255, 181, 71)
                            pdf.cell(0, 6, f"Q{idx}{topic_str}{score_str}", ln=True)

                            pdf.set_font("Arial", "B", 9)
                            pdf.set_text_color(0, 201, 167)
                            pdf.cell(0, 5, "Interviewer:", ln=True)
                            pdf.set_font("Arial", "", 9)
                            pdf.set_text_color(40, 40, 40)
                            pdf.multi_cell(0, 5, clean_for_pdf(q_text))

                            pdf.set_font("Arial", "B", 9)
                            pdf.set_text_color(100, 120, 150)
                            pdf.cell(0, 5, "Candidate:", ln=True)
                            pdf.set_font("Arial", "", 9)
                            pdf.set_text_color(40, 40, 40)
                            pdf.multi_cell(0, 5, clean_for_pdf(a_text))

                            if t_feedback:
                                pdf.set_font("Arial", "I", 8)
                                pdf.set_text_color(120, 120, 120)
                                pdf.multi_cell(0, 4, clean_for_pdf(f"Feedback: {t_feedback}"))

                            pdf.ln(3)
                        pdf.ln(4)

                    # 5. Strengths
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 201, 167)
                    pdf.cell(0, 8, "Strengths", ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(40, 40, 40)
                    if strengths_list:
                        for s in strengths_list:
                            pdf.cell(5, 6, "  * ", ln=False)
                            pdf.cell(0, 6, clean_for_pdf(str(s)), ln=True)
                    else:
                        pdf.cell(0, 6, "  * No specific strengths logged by the agent yet.", ln=True)
                    pdf.ln(4)

                    # 6. Weaknesses
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(230, 80, 80)
                    pdf.cell(0, 8, "Weaknesses", ln=True)
                    pdf.set_font("Arial", "", 10)
                    pdf.set_text_color(40, 40, 40)
                    if weaknesses_list:
                        for w in weaknesses_list:
                            pdf.cell(5, 6, "  * ", ln=False)
                            pdf.cell(0, 6, clean_for_pdf(str(w)), ln=True)
                    else:
                        pdf.cell(0, 6, "  * No critical weaknesses identified.", ln=True)
                    pdf.ln(4)

                    # 7. Decision Notes
                    pdf.set_font("Arial", "B", 12)
                    pdf.set_text_color(0, 201, 167)
                    pdf.cell(0, 8, "Decision Notes", ln=True)
                    pdf.set_font("Arial", "I", 10)
                    pdf.set_text_color(0, 168, 139)
                    pdf.multi_cell(0, 6, clean_for_pdf(decision_notes))
                    pdf.ln(6)

                    # 8. Topic Scores Chart
                    topics = ["Technical", "Communication", "Problem Solving", "Behavior"]
                    scores = [
                        score_value,
                        max(score_value - 4, 10),
                        max(score_value - 8, 15),
                        max(score_value - 12, 12),
                    ]

                    if turns_data:
                        t_scores = {"technical": [], "communication": [], "problem solving": [], "behavior": []}
                        for turn in turns_data:
                            t = str(turn.get("topic", "")).lower().strip()
                            s_val = turn.get("score", 0)
                            pct = (s_val / 5.0) * 100
                            if "tech" in t:
                                t_scores["technical"].append(pct)
                            elif "comm" in t:
                                t_scores["communication"].append(pct)
                            elif "prob" in t or "solve" in t:
                                t_scores["problem solving"].append(pct)
                            else:
                                t_scores["behavior"].append(pct)
                        scores = [
                            sum(t_scores["technical"]) / len(t_scores["technical"]) if t_scores["technical"] else score_value,
                            sum(t_scores["communication"]) / len(t_scores["communication"]) if t_scores["communication"] else score_value,
                            sum(t_scores["problem solving"]) / len(t_scores["problem solving"]) if t_scores["problem solving"] else score_value,
                            sum(t_scores["behavior"]) / len(t_scores["behavior"]) if t_scores["behavior"] else score_value,
                        ]

                    fig, ax = plt.subplots(figsize=(6, 3))
                    colors = ["#00C9A7", "#007BFF", "#FFB547", "#92A8BD"]
                    ax.bar(topics, scores, color=colors, width=0.5)
                    ax.set_title("Topic Scores", fontsize=12, fontweight="bold", pad=15)
                    ax.set_ylim(0, 100)
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)
                    ax.spines["left"].set_color("#cccccc")
                    ax.spines["bottom"].set_color("#cccccc")

                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmpfile:
                        plt.savefig(tmpfile.name, dpi=300, bbox_inches="tight", transparent=True)
                        plt.close(fig)
                        pdf.image(tmpfile.name, x=45, y=pdf.get_y(), w=120)

                    return pdf.output(dest="S").encode("latin-1")

                # ── Download button ──────────────────────────────────────────
                try:
                    pdf_bytes = generate_pdf()
                    st.download_button(
                        label=f"📥 Download Full Assessment & AI Analysis PDF for {candidate}",
                        data=pdf_bytes,
                        file_name=f"{candidate.replace(' ', '_')}_Evaluation_Report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                except Exception as pdf_err:
                    st.error(f"Error constructing live PDF data: {pdf_err}")

st.markdown('</div>', unsafe_allow_html=True)