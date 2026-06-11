import streamlit as st
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from pathlib import Path
st.set_page_config(page_title="Recruiter Panel", page_icon="💼", layout="wide")

# -----------------------------
# CSS
# -----------------------------
from styles import Dashboard_CSS
st.markdown(Dashboard_CSS, unsafe_allow_html=True)

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
    if st.button("Dashboard", key="nav_dashboard"):
        set_page("dashboard")

with col2:
    if st.button("Candidates", key="nav_candidates"):
        set_page("candidates")

with col3:
    if st.button("Reports", key="nav_reports"):
        set_page("reports")

st.markdown('</div>', unsafe_allow_html=True)

# -----------------------------
# PAGE CONTENT
# -----------------------------
st.markdown('<div class="section-box">', unsafe_allow_html=True)

# Load Excel once
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # Goes up to AI-Interview-Agent/
EXCEL_PATH = PROJECT_ROOT / "data" / "candidates.xlsx"
df = pd.read_excel(EXCEL_PATH)

# -----------------------------
# DASHBOARD PAGE 
# -----------------------------
if st.session_state.active_page == "dashboard":

    
    st.markdown("""
        <h2 style='text-align:center; 
                   font-weight:900; 
                   font-size:2.4rem;
                   background: linear-gradient(90deg,#4F46E5,#6366F1,#A78BFA);
                   -webkit-background-clip:text;
                   -webkit-text-fill-color:transparent;
                   margin-bottom:5px;'>
            📊 Dashboard Overview
        </h2>
        <p style='text-align:center; color:#6B7280; margin-bottom:40px;'>
            Real‑time insights into candidate performance and interview progress
        </p>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Stylish Metric Cards
    # -----------------------------
    st.markdown("""
        <style>
        .metric-card {
            background: rgba(255,255,255,0.75);
            backdrop-filter: blur(12px);
            padding: 25px;
            border-radius: 18px;
            text-align: center;
            border: 1px solid rgba(99,102,241,0.25);
            box-shadow: 0 8px 25px rgba(0,0,0,0.05);
            transition: 0.3s ease;
        }
        .metric-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 14px 35px rgba(79,70,229,0.25);
        }
        .metric-title {
            color: #4F46E5;
            font-size: 1rem;
            font-weight: 700;
        }
        .metric-value {
            color: #312E81;
            font-size: 2rem;
            font-weight: 900;
        }
        </style>
    """, unsafe_allow_html=True)

    total_candidates = len(df)
    completed = len(df[df["status"] == "Completed"])
    pending = len(df[df["status"] == "Pending"])
    avg_score = round(df["score"].mean(), 2)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Total Candidates</div>
                <div class='metric-value'>{total_candidates}</div>
            </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Completed</div>
                <div class='metric-value'>{completed}</div>
            </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Pending</div>
                <div class='metric-value'>{pending}</div>
            </div>
        """, unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>Average Score</div>
                <div class='metric-value'>{avg_score}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # -----------------------------
    # Charts Section
    # -----------------------------
    colA, colB = st.columns(2)

    with colA:
        st.markdown("""
            <h4 style='color:#4F46E5; font-weight:800;'>Status Distribution</h4>
        """, unsafe_allow_html=True)
        fig1 = px.pie(df, names="status", color="status",
                      color_discrete_map={"Completed": "#4F46E5", "Pending": "#A78BFA"})
        st.plotly_chart(fig1, use_container_width=True)

    with colB:
        st.markdown("""
            <h4 style='color:#4F46E5; font-weight:800;'>Candidates Scores</h4>
        """, unsafe_allow_html=True)
        fig2 = px.bar(df, x="name", y="score", color="score",
                      color_continuous_scale=["#A78BFA", "#4F46E5"])
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<br><hr><br>", unsafe_allow_html=True)

    # -----------------------------
    # Line Chart
    # -----------------------------
    df_line = df.copy()
    df_line["index"] = range(1, len(df_line) + 1)

    st.markdown("""
        <h4 style='color:#4F46E5; font-weight:800;'>Interview Progress Trend</h4>
    """, unsafe_allow_html=True)

    fig3 = px.line(df_line, x="index", y="score",
                   markers=True,
                   color_discrete_sequence=["#4F46E5"])
    st.plotly_chart(fig3, use_container_width=True)

# -----------------------------
# CANDIDATES PAGE 
# -----------------------------
elif st.session_state.active_page == "candidates":

    st.markdown("""
        <h1 style='text-align:center; 
                   font-weight:800; 
                   color:#4C1D95;
                   margin-bottom:10px;'>
            👥 Candidates Overview
        </h1>
        <p style='text-align:center; color:#6B7280; margin-bottom:40px;'>
            A modern dashboard displaying all candidate records.
        </p>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Stylish Metric Cards
    # -----------------------------
    st.markdown("""
        <style>
        .metric-box {
            background: linear-gradient(135deg, #EEF2FF, #E0E7FF);
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            border: 1px solid #C7D2FE;
            box-shadow: 0 4px 10px rgba(0,0,0,.05);
        }
        .metric-title {
            color: #4C1D95;
            font-size: 18px;
            font-weight: 700;
        }
        .metric-value {
            color: #6D28D9;
            font-size: 26px;
            font-weight: 800;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Total Candidates</div>
                <div class='metric-value'>{len(df)}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Completed</div>
                <div class='metric-value'>{df[df["status"] == "Completed"].shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Pending</div>
                <div class='metric-value'>{df[df["status"] == "Pending"].shape[0]}</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        avg_score = round(df["score"].mean(), 2)
        st.markdown(f"""
            <div class='metric-box'>
                <div class='metric-title'>Average Score</div>
                <div class='metric-value'>{avg_score}%</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # -----------------------------
    # Candidates Table
    # -----------------------------
    st.markdown("""
        <h3 style='color:#4C1D95; font-weight:700;'>📋 Candidates Table</h3>
        <p style='color:#6B7280;'>All candidate data loaded directly from Excel.</p>
    """, unsafe_allow_html=True)

    st.dataframe(df, use_container_width=True, height=400)

    # -----------------------------
    # Top 3 Candidates
    # -----------------------------
    st.markdown("""
        <h3 style='color:#4C1D95; font-weight:700; margin-top:40px;'>🏆 Top 3 Candidates</h3>
        <p style='color:#6B7280;'>Highest scoring candidates.</p>
    """, unsafe_allow_html=True)

    top3 = df.sort_values(by="score", ascending=False).head(3)

    st.dataframe(top3, use_container_width=True)

# -----------------------------
# REPORTS PAGE
# -----------------------------
elif st.session_state.active_page == "reports":

    st.subheader("📄 Candidate Reports")

    candidate = st.selectbox("Select Candidate", df["name"].tolist())

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
        if score_value >= 90:
            analysis = "Excellent performance"
            st.success("Excellent ✨")
        elif score_value >= 75:
            analysis = "Good performance"
            st.info("Very Good 👍")
        else:
            analysis = "Needs improvement"
            st.warning("Needs Improvement ⚠️")

    st.progress(progress_score)
    st.caption(f"**Status Analysis:** {analysis}")

    st.markdown("---")

    # -----------------------------
    # PDF Generator
    # -----------------------------
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
            pdf.cell(40, 10, f"{label}:", ln=False)
            pdf.set_font("Arial", "", 11)
            pdf.cell(0, 10, str(value), ln=True)
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
        pdf.multi_cell(0, 12, f"Result: {analysis}\nThis report is automatically generated.", border=1, fill=True)

        return pdf.output(dest="S").encode("latin-1")

    pdf_data = generate_pdf()

    st.download_button(
        "📄 Download Professional PDF Report",
        data=pdf_data,
        file_name=f"{candidate}_Assessment_Report.pdf",
        mime="application/pdf",
        use_container_width=True
    )

