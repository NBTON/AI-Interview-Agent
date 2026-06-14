import streamlit as st
import requests
st.set_page_config(page_title="Recruiter Login", page_icon="🔐", layout="centered")
API_URL = "http://localhost:8000/api"

# -----------------------------
# CSS 
# -----------------------------
from styles import Recruiter_Login_CSS
st.markdown(Recruiter_Login_CSS, unsafe_allow_html=True)


# -----------------------------
# UI/login
# -----------------------------
_, col2, _ = st.columns([1, 2, 1])

with col2:
    st.markdown("<div class='verify-card'>", unsafe_allow_html=True)
    st.markdown("<div class='verify-title'>Recruiter Login</div>", unsafe_allow_html=True)
    st.markdown("<div class='verify-sub'>Access candidate analytics and dashboards</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    email = st.text_input("Email", placeholder="e.g. admin@example.com")
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
                st.error("Please enter both email and password")

    with btn_col2:
        if st.button("Back to Home 🏠", use_container_width=True):
            st.switch_page("app.py")


