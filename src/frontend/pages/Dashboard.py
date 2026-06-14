import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from pathlib import Path
import requests
import io

# Page Config
st.set_page_config(page_title="Recruiter Panel", page_icon="💼", layout="wide")

# Auth Guard
if "recruiter_logged_in" not in st.session_state or not st.session_state["recruiter_logged_in"]:
    st.warning("Please log in to access the recruiter panel.")
    st.switch_page("pages/Recruiter_Login.py")
    st.stop()

# -----------------------------
# CSS
# -----------------------------
from styles import Dashboard_CSS
st.markdown(Dashboard_CSS, unsafe_allow_html=True)

# -----------------------------
# Sidebar with Log Out
# -----------------------------
st.sidebar.markdown("""
    <div style='text-align: center; margin-bottom: 20px;'>
        <img src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="80" style='border-radius: 50%; border: 3px solid #4F46E5; box-shadow: 0 4px 10px rgba(0,0,0,0.15);'>
        <h4 style='color: #1E1B4B; margin-top: 12px; margin-bottom: 0;'>HR Admin</h4>
        <p style='color: #6B7280; font-size: 13px;'>Admissions Team</p>
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
# Navigation Bar
# -----------------------------
st.markdown("### Welcome back, Admin!")
st.write("Access candidate reports and manage interview results easily.")

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
            # Standardize columns
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

# Helper function to remove emoji or non-latin-1 characters to prevent PDF crashes
def clean_for_pdf(text: str) -> str:
    cleaned = ""
    for char in str(text):
        if ord(char) < 256:
            cleaned += char
        else:
            if char == "—": cleaned += "-"
            elif char in ["“", "”"]: cleaned += '"'
            elif char in ["‘", "’"]: cleaned += "'"
            else: cleaned += "?"  # Fallback for emojis or other symbols
    return cleaned

# -----------------------------
# DASHBOARD PAGE 
# -----------------------------
if st.session_state.active_page == "dashboard":
    st.markdown("""
        <h2 style='text-align:center; font-weight:900; font-size:2.4rem; background: linear-gradient(90deg,#4F46E5,#6366F1,#8B5CF6); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:5px;'>
            📊 Dashboard Overview
        </h2>
        <p style='text-align:center; color:#6B7280; margin-bottom:40px;'>
            Real‑time insights into candidate performance and interview progress
        </p>
    """, unsafe_allow_html=True)

    if df.empty:
        st.warning("No candidate records found. Once candidates begin interviews, their metrics will appear here.")
    else:
        # Robust Status Counts
        completed = len(df[df["status"].str.lower().str.strip().isin(["completed", "accepted", "rejected", "interviewed"])])
        pending = len(df[df["status"].str.lower().str.strip().isin(["pending", "interviewing", "in_progress"])])
        avg_score = round(df["score"].mean(), 2)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Total Candidates</div><div class='metric-value'>{len(df)}</div></div>", unsafe_allow_html=True)
        with c2:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Completed</div><div class='metric-value'>{completed}</div></div>", unsafe_allow_html=True)
        with c3:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Pending/Active</div><div class='metric-value'>{pending}</div></div>", unsafe_allow_html=True)
        with c4:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Average Score</div><div class='metric-value'>{avg_score}%</div></div>", unsafe_allow_html=True)

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        colA, colB = st.columns(2)
        with colA:
            st.markdown("<h4 style='color:#4F46E5; font-weight:800;'>Status Distribution</h4>", unsafe_allow_html=True)
            color_discrete_map = {}
            for stat in df["status"].unique():
                s_lower = stat.lower().strip()
                if s_lower in ["completed", "accepted", "interviewed"]:
                    color_discrete_map[stat] = "#10B981"
                elif s_lower == "rejected":
                    color_discrete_map[stat] = "#EF4444"
                else:
                    color_discrete_map[stat] = "#6366F1"
            fig1 = px.pie(df, names="status", color="status", color_discrete_map=color_discrete_map)
            st.plotly_chart(fig1, use_container_width=True)

        with colB:
            st.markdown("<h4 style='color:#4F46E5; font-weight:800;'>Candidates Scores</h4>", unsafe_allow_html=True)
            fig2 = px.bar(df, x="name", y="score", color="score", color_continuous_scale=["#A78BFA", "#4F46E5"])
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("<br><hr><br>", unsafe_allow_html=True)

        st.markdown("<h4 style='color:#4F46E5; font-weight:800;'>Interview Progress Trend</h4>", unsafe_allow_html=True)
        df_line = df.copy()
        df_line["index"] = range(1, len(df_line) + 1)
        fig3 = px.line(df_line, x="index", y="score", markers=True, color_discrete_sequence=["#4F46E5"])
        st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# CANDIDATES PAGE 
# -----------------------------
elif st.session_state.active_page == "candidates":
    st.markdown("""
        <h1 style='text-align:center; font-weight:800; color:#4C1D95; margin-bottom:10px;'>
            👥 Candidates Overview
        </h1>
        <p style='text-align:center; color:#6B7280; margin-bottom:40px;'>
            A modern dashboard displaying all candidate records.
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
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Pending/Active</div><div class='metric-value'>{pending}</div></div>", unsafe_allow_html=True)
        with col4:
            st.markdown(f"<div class='metric-card'><div class='metric-title'>Average Score</div><div class='metric-value'>{avg_score}%</div></div>", unsafe_allow_html=True)

        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown("<h3 style='color:#4C1D95; font-weight:700;'>📋 Candidates Table</h3>", unsafe_allow_html=True)
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

        st.markdown("<h3 style='color:#4C1D95; font-weight:700; margin-top:40px;'>🏆 Top Candidates</h3>", unsafe_allow_html=True)
        top3 = df.sort_values(by="score", ascending=False).head(3)
        st.dataframe(top3, use_container_width=True)

# -----------------------------
# REPORTS PAGE
# -----------------------------
elif st.session_state.active_page == "reports":
    st.subheader("📄 Candidate Reports")

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

            st.markdown(f"### 👤 Candidate: {candidate}")

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

            st.markdown("---")

            # PDF Generator
            class PDF(FPDF):
                def header(self):
                    self.set_fill_color(26, 54, 93)
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
                pdf.set_text_color(26, 54, 93)
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
