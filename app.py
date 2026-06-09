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

body {
    background: linear-gradient(135deg, #EEF2FF, #E0E7FF, #C7D2FE);
    background-size: 300% 300%;
    animation: gradientMove 10s ease infinite;
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
    font-size: 3.6rem;
    background: linear-gradient(90deg, #4F46E5, #6366F1, #A78BFA);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 18px rgba(99,102,241,0.25);
    animation: fadeIn 1.2s ease-in-out;
}

.subtitle {
    text-align: center;
    font-size: 1.35rem;
    color: #4B5563;
    margin-bottom: 55px;
    animation: fadeIn 1.6s ease-in-out;
}


.custom-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(14px);
    padding: 40px;
    border-radius: 26px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
    text-align: center;
    transition: all 0.35s ease;
    border: 1px solid rgba(99,102,241,0.35);
}

.custom-card:hover {
    transform: translateY(-12px) scale(1.03);
    box-shadow: 0 25px 55px rgba(79,70,229,0.35);
    border-color: #4F46E5;
    
}

.card-icon {
    margin-bottom: 25px;
    filter: drop-shadow(0 6px 12px rgba(0,0,0,0.15));
}

.card-title {
    font-size: 1.75rem;
    font-weight: 800;
    color: #312E81;
    margin-bottom: 12px;
}


.card-desc {
    font-size: 1.1rem;
    color: #4B5563;
    margin-bottom: 25px;
    min-height: 50px;
}


div.stButton > button {
    background: linear-gradient(135deg, #4F46E5 0%, #4338CA 100%) !important;
    color: white !important;
    font-weight: 800 !important;
    padding: 15px 28px !important;
    border-radius: 16px !important;
    border: none !important;
    transition: 0.3s ease !important;
    box-shadow: 0 6px 18px rgba(79,70,229,0.35);
    letter-spacing: 0.5px;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #4338CA 0%, #3730A3 100%) !important;
    transform: translateY(-4px);
    box-shadow: 0 10px 28px rgba(55,48,163,0.55);
}

div.stButton {
    margin-top: 50px;
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

