import streamlit as st
import requests
# pages 
st.set_page_config(page_title="Candidate Verification", page_icon="📝", layout="centered")
API_URL = "http://localhost:8000/api"
# -----------------------------
# CSS 
# -----------------------------
from styles import Candidate_CSS
st.markdown(Candidate_CSS, unsafe_allow_html=True)

# -----------------------------
# UI/verify
# -----------------------------
_, col2, _ = st.columns([1, 2, 1])

with col2:
    st.markdown("<div class='verify-card'>", unsafe_allow_html=True)
    st.markdown("<div class='verify-title'>Candidate Verification</div>", unsafe_allow_html=True)
    st.markdown("<div class='verify-sub'>Please enter your registered email to continue</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    email = st.text_input("Email Address", placeholder="e.g. ali@example.com")

    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        if st.button("Verify Check ✔️", use_container_width=True):
            if email.strip():
                try:
                    response = requests.post(f"{API_URL}/candidates/verify", json={"email": email})
                    if response.status_code == 200:
                        data = response.json()
                        st.success(data["message"])
                        st.session_state["candidate_name"] = data["name"]
                        st.session_state["candidate_email"] = email
                        st.switch_page("pages/Interview.py")
                    else:
                        st.error(response.json().get("detail", "Email not found"))
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Make sure the server is running.")
                except Exception as e:
                    st.error(f"Verification error: {str(e)}")
            else:
                st.error("Please enter email")
                
    with btn_col2:
        if st.button("Back to Home 🏠", use_container_width=True):
            st.switch_page("app.py")

