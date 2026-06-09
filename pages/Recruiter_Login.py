import streamlit as st

st.set_page_config(page_title="Recruiter Login", page_icon="🔐", layout="centered")

# -----------------------------
# CSS 
# -----------------------------
st.markdown("""
<style>




.login-title {
    text-align: center;
    font-size: 28px;
    font-weight: 800;
    color: #5B21B6;
    margin-bottom: 10px;
}

.login-sub {
    text-align: center;
    color: #6B7280;
    margin-bottom: 25px;
}

.stTextInput > div > div > input {
    border-radius: 10px;
    border: 1px solid #C4B5FD;
}

.stButton button {
    background: linear-gradient(90deg, #6C63FF, #8B5CF6);
    color: white;
    border-radius: 10px;
    height: 48px;
    width: 100%;
    border: none;
    font-weight: 700;
    transition: 0.2s;
}

.stButton button:hover {
    opacity: 0.9;
    transform: translateY(-2px);
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# data input
# -----------------------------
VALID_EMAIL = "admin@example.com"
VALID_PASSWORD = "12345"

# -----------------------------
# UI/login
# -----------------------------
st.markdown("<div class='login-card'>", unsafe_allow_html=True)

st.markdown("<div class='login-title'>Recruiter Login</div>", unsafe_allow_html=True)
st.markdown("<div class='login-sub'>Please enter your credentials to continue</div>", unsafe_allow_html=True)

email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):

    if email == VALID_EMAIL and password == VALID_PASSWORD:
        st.success("Login successful")
        st.session_state["recruiter_logged_in"] = True
        st.switch_page("pages/Dashboard.py")
    else:
        st.error("Incorrect email or password")

st.markdown("</div>", unsafe_allow_html=True)

