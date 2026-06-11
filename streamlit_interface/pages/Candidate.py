import streamlit as st
import pandas as pd
from pathlib import Path
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
#UI/verify
# -----------------------------
st.markdown("<div class='verify-card'>", unsafe_allow_html=True)
st.markdown("<div class='verify-title'>Candidate Verification</div>", unsafe_allow_html=True)
st.markdown("<div class='verify-sub'>Please enter your registered email to continue</div>", unsafe_allow_html=True)

#read Excel
PROJECT_ROOT = Path(__file__).resolve().parents[2]
excel_file = PROJECT_ROOT / "data" / "candidates.xlsx"
df = pd.read_excel(excel_file)
email = st.text_input("Email Address")

# if st.button("Verify"):

#     if email.strip():

#         #check if email exists in the DataFrame
#         match = df[df["email"] == email]

#         if not match.empty:
#             st.success("Email Verified Successfully")

#             # extract the actual name from the Excel file
#             candidate_name = match.iloc[0]["name"]

#             # save the name in Session State
#             st.session_state["candidate_name"] = candidate_name

#             # to chat page
#             st.switch_page("pages/Chatbot.py")

#         else:
#             st.error("Email not found. Please contact HR.")

#     else:
#         st.error("Please enter email")
if st.button("Verify"):
    if email.strip():
        response = requests.post(f"{API_URL}/candidates/verify", json={"email": email})
        if response.status_code == 200:
            data = response.json()
            st.success(data["message"])
            st.session_state["candidate_name"] = data["name"]
            st.switch_page("pages/Chatbot.py")
        else:
            st.error(response.json().get("detail", "Email not found"))
st.markdown("</div>", unsafe_allow_html=True)


