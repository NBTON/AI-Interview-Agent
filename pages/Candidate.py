import streamlit as st
import pandas as pd

# pages 
st.set_page_config(page_title="Candidate Verification", page_icon="📝", layout="centered")

# -----------------------------
# CSS 
# -----------------------------
st.markdown("""
<style>

body {
    background-color: #F5F3FF;
}


.verify-title {
    text-align: center;
    font-size: 28px;
    font-weight: 800;
    color: #5B21B6;
    margin-bottom: 10px;
}

.verify-sub {
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
#UI/verify
# -----------------------------
st.markdown("<div class='verify-card'>", unsafe_allow_html=True)

st.markdown("<div class='verify-title'>Candidate Verification</div>", unsafe_allow_html=True)
st.markdown("<div class='verify-sub'>Please enter your registered email to continue</div>", unsafe_allow_html=True)

#read Excel
df = pd.read_excel("data/candidates.xlsx")

email = st.text_input("Email Address")

if st.button("Verify"):

    if email.strip():

        #check if email exists in the DataFrame
        match = df[df["email"] == email]

        if not match.empty:
            st.success("Email Verified Successfully")

            # extract the actual name from the Excel file
            candidate_name = match.iloc[0]["name"]

            # save the name in Session State
            st.session_state["candidate_name"] = candidate_name

            # to chat page
            st.switch_page("pages/Chatbot.py")

        else:
            st.error("Email not found. Please contact HR.")

    else:
        st.error("Please enter email")

st.markdown("</div>", unsafe_allow_html=True)


