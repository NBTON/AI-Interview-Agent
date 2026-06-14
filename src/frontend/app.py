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
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Outfit', sans-serif !important;
    background: linear-gradient(135deg, #EEF2FF, #E0E7FF, #C7D2FE) !important;
    background-size: 300% 300% !important;
    animation: gradientMove 15s ease infinite !important;
}

/* background */
@keyframes gradientMove {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

/* hide streamlit elements */
#MainMenu, footer, header {visibility: hidden;}

/*  title */
.main-title {
    text-align: center;
    font-weight: 900;
    font-size: 4rem;
    background: linear-gradient(90deg, #4F46E5, #6366F1, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 30px rgba(99,102,241,0.15);
    margin-top: 40px;
    margin-bottom: 5px;
    animation: fadeIn 1.2s ease-in-out;
}

.subtitle {
    text-align: center;
    font-size: 1.4rem;
    color: #4B5563;
    margin-bottom: 60px;
    animation: fadeIn 1.6s ease-in-out;
}

.custom-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 45px 35px;
    border-radius: 28px;
    box-shadow: 0 15px 35px rgba(0,0,0,0.06);
    text-align: center;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    border: 1px solid rgba(99,102,241,0.2);
}

.custom-card:hover {
    transform: translateY(-8px) scale(1.02);
    box-shadow: 0 30px 60px rgba(79,70,229,0.18);
    border-color: rgba(99,102,241,0.55);
}

.card-icon {
    margin-bottom: 25px;
    filter: drop-shadow(0 8px 16px rgba(99,102,241,0.15));
}

.card-title {
    font-size: 1.95rem;
    font-weight: 800;
    color: #1E1B4B;
    margin-bottom: 12px;
}

.card-desc {
    font-size: 1.1rem;
    color: #4B5563;
    margin-bottom: 25px;
    min-height: 55px;
    line-height: 1.5;
}

div.stButton > button {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 14px 28px !important;
    border-radius: 14px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 6px 20px rgba(79,70,229,0.25) !important;
    font-size: 16px !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 10px 25px rgba(79,70,229,0.4) !important;
}

div.stButton {
    margin-top: 20px;
}

/* Animation */
@keyframes fadeIn {
    from {opacity: 0; transform: translateY(12px);}
    to {opacity: 1; transform: translateY(0);}
}

</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown('<h1 class="main-title">AI Interview Platform</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Smart • Elegant • AI‑Powered Interview Experience</p>', unsafe_allow_html=True)

# --- Layout ---
_, col1, _, col2, _ = st.columns([1, 2, 0.5, 2, 1])

# --- Candidate Portal ---
with col1:
    st.markdown("""
        <div class="custom-card">
            <img class="card-icon" src="https://cdn-icons-png.flaticon.com/512/9463/9463200.png" width="110">
            <div class="card-title">Start Interview</div>
            <div class="card-desc">Verify your identity and begin your AI‑powered interview session.</div>
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
