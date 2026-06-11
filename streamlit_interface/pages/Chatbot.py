import streamlit as st
import requests

st.set_page_config(page_title="Interview Chat", page_icon="💬", layout="wide")

# Guard: redirect if no candidate verified
if "candidate_name" not in st.session_state:
    st.warning("Please verify your identity first.")
    st.switch_page("pages/Candidate.py")
    st.stop()

API_URL = "http://localhost:8000/api"

# -----------------------------
# CSS 
# -----------------------------
from styles import Chatbot_CSS
st.markdown(Chatbot_CSS, unsafe_allow_html=True)


# Initialize session state for messages if not exists
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize interview session if not exists and candidate_name is available
if "session_id" not in st.session_state and "candidate_name" in st.session_state:
    try:
        response = requests.post(f"{API_URL}/interview/start", json={
            "candidate_name": st.session_state["candidate_name"],
            "candidate_email": st.session_state.get("candidate_email", st.session_state.get("candidate_name", "candidate").lower().replace(" ", "") + "@example.com")
        })
        
        if response.status_code == 200:
            data = response.json()
            st.session_state["session_id"] = data["session_id"]
            # Add welcome message and first question
            st.session_state.messages = [
                {"role": "bot", "text": f"Hello {st.session_state['candidate_name']}, welcome to your AI interview."},
                {"role": "bot", "text": data["first_question"]}
            ]
        else:
            st.error(f"Failed to start interview: {response.json().get('detail', 'Unknown error')}")
            st.stop()
    except Exception as e:
        st.error(f"Error connecting to backend: {str(e)}")
        st.info("Make sure the backend server is running on http://localhost:8000")
        st.stop()

# Get candidate name
name = st.session_state.get("candidate_name", "Candidate")

# -----------------------------
# page layout
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

    # Display all messages
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
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "text": user_input})
            
            # Show thinking state
            with st.spinner("Analyzing your answer..."):
                try:
                    # Send to backend
                    response = requests.post(f"{API_URL}/interview/answer", json={
                        "session_id": st.session_state["session_id"],
                        "answer": user_input
                    })
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        if data["is_complete"]:
                            # Interview complete
                            st.session_state.messages.append({
                                "role": "bot", 
                                "text": f"🎉 Interview complete! Your score: {data['final_score']:.1f}%"
                            })
                            st.success(f"Interview completed! Final score: {data['final_score']:.1f}%")
                        else:
                            # Add bot response
                            st.session_state.messages.append({
                                "role": "bot", 
                                "text": data["next_question"]
                            })
                            # Optional: Show feedback
                            if data.get("feedback"):
                                st.info(f"💡 Feedback: {data['feedback']}")
                    else:
                        st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                        
                except Exception as e:
                    st.error(f"Error connecting to backend: {str(e)}")
            
            # Clear input key from session state
            st.session_state["chat_input"] = ""
            # Clear input by rerunning
            st.rerun()

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
    
    # Show progress if session exists
    if "session_id" in st.session_state:
        try:
            response = requests.get(f"{API_URL}/interview/session/{st.session_state['session_id']}")
            if response.status_code == 200:
                session_data = response.json()
                current_q = session_data.get("question_number", 1)
                total_q = session_data.get("total_questions", 5)
                progress = (current_q - 1) / total_q
                
                st.write(f"**Question:** {current_q}/{total_q}")
                st.progress(progress)
                
                if session_data.get("average_score", 0) > 0:
                    st.write(f"**Current Score:** {session_data['average_score']:.1f}%")
        except:
            st.write("**Interview Progress:** In progress")
    
    st.markdown('<div class="progress-circle"></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)