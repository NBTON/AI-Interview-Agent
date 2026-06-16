import streamlit as st
 
#page
st.set_page_config(
    page_title="AI Interview Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed"
)
 
#  CSS 
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
 
#MainMenu, footer, header { visibility: hidden; }
 
.main-title {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    font-weight: 900;
    font-size: 3.8rem;
    color: #E8EDF3;
    text-shadow: 0 0 60px rgba(0, 201, 167, 0.2);
    margin-top: 40px;
    margin-bottom: 6px;
    animation: fadeIn 1.2s ease-in-out;
    letter-spacing: -1px;
}
 
.main-title span { color: #00C9A7; }
 
.subtitle {
    text-align: center;
    font-size: 1.2rem;
    color: #8FA4BE;
    margin-bottom: 60px;
    animation: fadeIn 1.6s ease-in-out;
    letter-spacing: 0.5px;
    font-weight: 400;
}
 
.custom-card {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    padding: 44px 36px;
    border-radius: 22px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    text-align: center;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    border: 1px solid rgba(143, 164, 190, 0.1);
}
 
.custom-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 32px 70px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 201, 167, 0.3);
    border-color: rgba(0, 201, 167, 0.28);
}
 
.card-icon {
    margin-bottom: 22px;
    filter: drop-shadow(0 8px 20px rgba(0, 201, 167, 0.2));
}
 
.card-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.85rem;
    font-weight: 800;
    color: #E8EDF3;
    margin-bottom: 10px;
    letter-spacing: -0.3px;
}
 
.card-desc {
    font-size: 1rem;
    color: #8FA4BE;
    margin-bottom: 22px;
    min-height: 52px;
    line-height: 1.6;
    font-weight: 400;
}
 
div.stButton > button {
    background: linear-gradient(135deg, #00C9A7 0%, #00A88B 100%) !important;
    color: #0A1628 !important;
    font-weight: 700 !important;
    padding: 14px 28px !important;
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
 
div.stButton { margin-top: 20px; }
 
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)
 
# --- Header ---
st.markdown('<h1 class="main-title">AI Interview <span>Platform</span></h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Smart · Elegant · AI-Powered Interview Experience</p>', unsafe_allow_html=True)
 
# --- Layout ---
_, col1, _, col2, _ = st.columns([1, 2, 0.5, 2, 1])
 
# --- Candidate Portal ---
with col1:
    st.markdown("""
        <div class="custom-card">
            <img class="card-icon" src="https://cdn-icons-png.flaticon.com/512/9463/9463200.png" width="110">
            <div class="card-title">Start Interview</div>
            <div class="card-desc">Verify your identity and begin your AI-powered interview session.</div>
        </div>
    """, unsafe_allow_html=True)
 
    if st.button("Begin Interview 🚀", key="btn_candidate", use_container_width=True):
        st.switch_page("pages/Candidate.py")
 
# --- Recruiter Portal ---
with col2:
    st.markdown("""
        <div class="custom-card">
            <img class="card-icon" src="https://cdn-icons-png.flaticon.com/512/3135/3135715.png" width="110">
            <div class="card-title">Recruiter Space</div>
            <div class="card-desc">Manage candidates, review analytics, and oversee interview progress.</div>
        </div>
    """, unsafe_allow_html=True)
 
    if st.button("Recruiter Login 💼", key="btn_recruiter", use_container_width=True):
        st.switch_page("pages/Recruiter_Login.py")