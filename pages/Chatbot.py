import streamlit as st


st.set_page_config(page_title="Interview Chat", page_icon="💬", layout="wide")

# Candidate name from Session State
if "candidate_name" not in st.session_state:
    st.session_state["candidate_name"] = "Candidate"

name = st.session_state["candidate_name"]

# -----------------------------
# CSS 
# -----------------------------
st.markdown("""
<style>

.msg-row {
    display: flex;
    align-items: flex-start;
    margin-bottom: 12px;
}

.msg-avatar {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    margin-right: 10px;
}

.msg-bubble-user {
    background-color: #6d28d9;
    color: white;
    padding: 10px 16px;
    border-radius: 12px;
    max-width: 70%;
}

.msg-bubble-bot {
    background-color: #f3f4f6;
    color: #374151;
    padding: 10px 16px;
    border-radius: 12px;
    max-width: 70%;
}

.side-card {
    background-color: #eef2ff;
    padding: 25px;
    border-radius: 15px;
    border: 1px solid #c7d2fe;
    text-align: center;
}

.side-card h4 {
    color: #4338ca;
    font-weight: 700;
}

.progress-circle {
    width: 110px;
    height: 110px;
    border-radius: 50%;
    border: 8px solid #e0e7ff;
    border-top-color: #4338ca;
    animation: spin 2s linear infinite;
    margin: auto;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

</style>
""", unsafe_allow_html=True)


# -----------------------------
#page layout
# -----------------------------
col1, col2 = st.columns([3, 1])

# -----------------------------
# chat interface
# -----------------------------
with col1:

    st.markdown(f"### 👋 Welcome, **{name}**")
    st.markdown("#### Your AI Interview Has Started")

    # chat box
    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    # start with 2 bot messages
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "bot", "text": f"Hello {name}, welcome to your AI interview."},
            {"role": "bot", "text": "Let's begin with a simple question: Tell me about yourself."},
        ]

    # messages display
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(
                f"""
                <div class="msg-row">
                    <img class="msg-avatar" src="https://cdn-icons-png.flaticon.com/512/9131/9131529.png">
                    <div class="msg-bubble-user">{msg["text"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="msg-row">
                    <img class="msg-avatar" src="https://cdn-icons-png.flaticon.com/512/4712/4712100.png">
                    <div class="msg-bubble-bot">{msg["text"]}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # user input
    user_input = st.text_input("Write your answer...", key="chat_input")

    if st.button("Send"):
        if user_input.strip():
            st.session_state.messages.append({"role": "user", "text": user_input})
            st.session_state.messages.append({"role": "bot", "text": "Thank you for your answer. Let's continue."})

# -----------------------------
# Candidate Information Column
# -----------------------------
with col2:
    st.markdown("""
        <div class="side-card">
            <img src="https://cdn-icons-png.flaticon.com/512/9131/9131529.png" width="80">
            <h4>Candidate Information</h4>
    """, unsafe_allow_html=True)

    st.write(f"**Name:** {name}")
    st.write("**Bootcamp:** Agentic AI")
    st.write("**Interview Progress:**")

    st.markdown('<div class="progress-circle"></div>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)
