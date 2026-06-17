import streamlit as st
import requests

st.set_page_config(page_title="Recruiter Login", page_icon="🔐", layout="centered")

API_URL = "http://localhost:8000/api"

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
    from { opacity: 0; transform: translateY(14px); }
    to   { opacity: 1; transform: translateY(0); }
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 3rem !important; }

/* Glass card */
.login-card {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    padding: 48px 44px;
    border-radius: 22px;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    border: 1px solid rgba(143, 164, 190, 0.1);
    animation: fadeIn 1s ease-in-out;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.login-card:hover {
    box-shadow: 0 32px 70px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 201, 167, 0.22);
    border-color: rgba(0, 201, 167, 0.2);
}

.login-icon {
    text-align: center;
    margin-bottom: 20px;
    filter: drop-shadow(0 8px 20px rgba(0, 201, 167, 0.2));
}

.login-title {
    text-align: center;
    font-family: 'Outfit', sans-serif;
    font-size: 26px;
    font-weight: 800;
    color: #E8EDF3;
    letter-spacing: -0.4px;
    margin-bottom: 6px;
}

.login-sub {
    text-align: center;
    color: #8FA4BE;
    font-size: 14px;
    margin-bottom: 30px;
    line-height: 1.5;
}

/* Divider line inside card */
.card-divider {
    border: none;
    border-top: 1px solid rgba(143, 164, 190, 0.1);
    margin: 0 0 24px;
}

/* Inputs */
.stTextInput label, .stTextInput label p {
    color: #8FA4BE !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.8px !important;
}
.stTextInput > div > div > input {
    background: rgba(10, 22, 40, 0.75) !important;
    border: 1px solid rgba(143, 164, 190, 0.2) !important;
    border-radius: 12px !important;
    padding: 12px 16px !important;
    font-size: 15px !important;
    color: #E8EDF3 !important;
    font-family: 'Inter', sans-serif !important;
    transition: all 0.2s ease !important;
}
.stTextInput > div > div > input::placeholder { color: #4A6280 !important; }
.stTextInput > div > div > input:focus {
    border-color: #00C9A7 !important;
    box-shadow: 0 0 0 3px rgba(0, 201, 167, 0.12) !important;
    outline: none !important;
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
    width: 100% !important;
}
div.stButton > button:hover {
    background: linear-gradient(135deg, #00DFBB 0%, #00C9A7 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 12px 32px rgba(0, 201, 167, 0.42) !important;
}
div.stButton > button:active { transform: translateY(0) !important; }

/* Ghost back button */
div.stButton:nth-of-type(2) > button {
    background: transparent !important;
    border: 1px solid rgba(143, 164, 190, 0.25) !important;
    color: #8FA4BE !important;
    box-shadow: none !important;
}
div.stButton:nth-of-type(2) > button:hover {
    background: rgba(143, 164, 190, 0.07) !important;
    border-color: rgba(143, 164, 190, 0.45) !important;
    box-shadow: none !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stAlert"] { border-radius: 12px !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# UI
# -----------------------------
_, col2, _ = st.columns([1, 2, 1])

with col2:
    st.markdown("""
        <div class='login-card'>
            <div class='login-icon'>
                <img src='https://cdn-icons-png.flaticon.com/512/3135/3135715.png' width='72'>
            </div>
            <div class='login-title'>Recruiter Login</div>
            <div class='login-sub'>Access candidate analytics, reports, and interview dashboards.</div>
            <hr class='card-divider'>
        </div>
    """, unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="e.g. recruiter@example.com")
    password = st.text_input("Password", type="password", placeholder="Enter your password")

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Login 🔑", use_container_width=True):
            if email.strip() and password.strip():
                try:
                    response = requests.post(
                        f"{API_URL}/recruiter/login",
                        json={"email": email, "password": password}
                    )
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data["message"])
                        st.session_state["recruiter_logged_in"] = True
                        st.switch_page("pages/Dashboard.py")
                    else:
                        error_msg = response.json().get("detail", "Invalid credentials")
                        st.error(error_msg)
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the server is running.")
                except Exception as e:
                    st.error(f"Login error: {str(e)}")
            else:
                st.error("Please enter both email and password.")

    with btn_col2:
        if st.button("Back to Home", use_container_width=True):
            st.switch_page("app.py")
