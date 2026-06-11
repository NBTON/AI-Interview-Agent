import streamlit as st
import requests
st.set_page_config(page_title="Recruiter Login", page_icon="🔐", layout="centered")
API_URL = "http://localhost:8000/api"

# -----------------------------
# CSS 
# -----------------------------
from styles import Recruiter_Login_CSS
st.markdown(Recruiter_Login_CSS, unsafe_allow_html=True)


email = st.text_input("Email")
password = st.text_input("Password", type="password")

if st.button("Login"):
    if email.strip() and password.strip():
        try:
            # Call backend API instead of hardcoded check
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

st.markdown("</div>", unsafe_allow_html=True)

