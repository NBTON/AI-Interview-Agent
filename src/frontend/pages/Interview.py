import streamlit as st
import requests
import sys
import io
import html

st.set_page_config(page_title="AI Interview Session", page_icon=":material/assignment:", layout="wide")

# Guard: redirect if no candidate verified
if "candidate_name" not in st.session_state:
    st.warning("Please verify your identity first.")
    st.switch_page("pages/Candidate.py")
    st.stop()

API_URL = "http://localhost:8000/api"
API_TIMEOUT = 125

# -----------------------------
# CSS 
# -----------------------------
from styles import Chatbot_CSS
st.markdown(Chatbot_CSS, unsafe_allow_html=True)

def _safe_detail(response, default="The interview service is temporarily unavailable. Please try again."):
    try:
        detail = response.json().get("detail")
    except Exception:
        detail = None

    if response.status_code in (404, 422) and detail:
        return str(detail)
    return default

if "session_id" not in st.session_state:
    try:
        response = requests.post(f"{API_URL}/interview/start", json={
            "candidate_name": st.session_state["candidate_name"],
            "candidate_email": st.session_state.get("candidate_email", "candidate@example.com")
        }, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            st.session_state["session_id"] = data["session_id"]
            
            # Setup current question state
            st.session_state["current_question_text"] = data["first_question"]
            st.session_state["current_question_type"] = data.get("question_type", "open_ended")
            st.session_state["current_options"] = data.get("options")
            st.session_state["current_initial_code"] = data.get("initial_code")
            st.session_state["current_topic"] = data.get("current_topic", "background")
            st.session_state["current_question_number"] = data.get("question_number", 1)
            st.session_state["current_total_questions"] = data.get("total_questions", 5)
            st.session_state["interview_is_complete"] = False
            st.session_state["final_score"] = None
        else:
            st.error(_safe_detail(response, "We could not start the interview right now. Please try again."))
            st.stop()
    except requests.exceptions.ConnectionError:
        st.error("We could not connect to the interview service. Please try again shortly.")
        st.stop()
    except requests.exceptions.Timeout:
        st.error("The interview service is taking longer than expected. Please try again.")
        st.stop()
    except Exception as e:
        st.error("We could not start the interview right now. Please try again.")
        st.stop()

# Get state variables
session_id = st.session_state["session_id"]
name = st.session_state["candidate_name"]
current_type = st.session_state.get("current_question_type", "open_ended")
current_number = st.session_state.get("current_question_number", 1)
is_complete = st.session_state.get("interview_is_complete", False)

QUESTION_TYPE_LABELS = {
    "text": "Open Ended",
    "open_ended": "Open Ended",
    "multiple_choice": "MCQ",
    "mcq": "MCQ",
    "true_false": "True or False",
    "coding": "Coding",
}

# Initialize editor state variables for coding exercises
if current_type == "coding":
    if "last_q_number" not in st.session_state:
        st.session_state["last_q_number"] = 0
        
    if current_number != st.session_state["last_q_number"]:
        st.session_state["user_code_input"] = st.session_state.get("current_initial_code", "")
        st.session_state["last_q_number"] = current_number
        st.session_state["console_output"] = ""
        st.session_state["console_success"] = None

# Python local code executor
def run_user_code(code: str):
    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    error_msg = ""
    success = False
    try:
        compiled = compile(code, "<string>", "exec")
        local_vars = {}
        exec(compiled, {}, local_vars)
        success = True
    except Exception as e:
        error_msg = str(e)
    finally:
        sys.stdout = old_stdout
        
    output_text = redirected_output.getvalue()
    return success, output_text, error_msg

# Page Layout
col1, col2 = st.columns([3, 1])

# -----------------------------
# QUESTIONNAIRE PANEL (Left Column)
# -----------------------------
with col1:
    if is_complete:
        st.markdown(
            """
            <div class='thank-you-card'>
                <img src='https://cdn-icons-png.flaticon.com/512/190/190411.png' width='100'>
                <div class='thank-you-title'>Thank You!</div>
                <div class='thank-you-text'>
                    Thank you for completing the interview assessment. 
                    Your responses have been successfully recorded and submitted. 
                    The admissions team will review your application and contact you soon.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Centered Back to Home Button
        _, btn_col, _ = st.columns([1, 1, 1])
        with btn_col:
            if st.button("Return to Home 🏠"):
                st.session_state.clear()
                st.switch_page("app.py")
    else:
        # Determine topic display label
        topic_raw = st.session_state.get("current_topic", "General")
        # In start phase, current_topic might not be set yet. Infer from missing_info or display General
        if not topic_raw or topic_raw == "General":
            try:
                response = requests.get(f"{API_URL}/interview/session/{session_id}", timeout=10)
                if response.status_code == 200:
                    topic_raw = response.json().get("current_topic", "General")
            except:
                pass
        
        if not topic_raw or topic_raw == "":
            topic_raw = "Background"
            
        topic_display = topic_raw.replace("_", " ").title()

        # Question card header
        question_type_display = QUESTION_TYPE_LABELS.get(current_type, current_type.replace("_", " ").title())
        st.markdown(
            f"""
            <div class='question-panel'>
                <div class='question-header'>
                    <div class='question-type'>{question_type_display}</div>
                    <div class='question-topic'>Topic: {topic_display}</div>
                </div>
                <div class='question-prompt'>{html.escape(str(st.session_state.get("current_question_text") or ""))}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Input controls depending on type
        submit_clicked = False
        user_answer_value = ""
        answer_key = f"{session_id}_{current_number}_{current_type}"
        
        # Support both 'text' and 'open_ended' type names
        if current_type in ["text", "open_ended"]:
            user_answer_value = st.text_area("Write your response:", key=f"txt_answer_{answer_key}", height=180, placeholder="Type your answer here...")
            st.write("")
            if st.button("Next Question", key=f"btn_next_{answer_key}"):
                submit_clicked = True
                
        elif current_type in ["multiple_choice", "mcq"]:
            options = st.session_state.get("current_options", [])
            selected_option = st.radio("Choose the correct option:", options, key=f"radio_options_{answer_key}", index=None)
            user_answer_value = selected_option if selected_option else ""
            st.write("")
            if st.button("Next Question", key=f"btn_next_{answer_key}"):
                submit_clicked = True
                
        elif current_type == "true_false":
            selected_tf = st.radio("Select True or False:", ["True", "False"], key=f"radio_tf_{answer_key}", index=None, horizontal=True)
            user_answer_value = selected_tf if selected_tf else ""
            st.write("")
            if st.button("Next Question", key=f"btn_next_{answer_key}"):
                submit_clicked = True
                
        elif current_type == "likert_scale":
            options = st.session_state.get("current_options") or [
                "1 - Strongly Disagree", 
                "2 - Disagree", 
                "3 - Neutral", 
                "4 - Agree", 
                "5 - Strongly Agree"
            ]
            selected_likert = st.radio("Select Rating:", options, key=f"radio_likert_{answer_key}", index=None, horizontal=True)
            user_answer_value = selected_likert if selected_likert else ""
            st.write("")
            if st.button("Next Question", key=f"btn_next_{answer_key}"):
                submit_clicked = True
                
        elif current_type == "coding":
            st.markdown(
                """
                <div class='ide-shell'>
                    <div class='ide-titlebar'>
                        <span class='ide-dot red'></span>
                        <span class='ide-dot yellow'></span>
                        <span class='ide-dot green'></span>
                        <span class='ide-filename'>solution.py</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            user_code = st.text_area("Code editor", value=st.session_state.get("user_code_input", ""), height=320, key=f"editor_pane_{answer_key}", label_visibility="collapsed")
            st.session_state["user_code_input"] = user_code
            user_answer_value = user_code
            
            st.write("")
            c_btn1, c_btn2 = st.columns([1, 1])
            with c_btn1:
                if st.button("Run & Test Code", use_container_width=True, key=f"btn_run_{answer_key}"):
                    success, stdout, stderr = run_user_code(user_code)
                    st.session_state["console_success"] = success
                    if success:
                        st.session_state["console_output"] = f"Code executed successfully.\n\nOutput:\n{stdout if stdout else '[No output printed]'}"
                    else:
                        st.session_state["console_output"] = f"Runtime Error:\n{stderr}"
                    st.rerun()
            with c_btn2:
                if st.button("Next Question", use_container_width=True, key=f"btn_next_{answer_key}"):
                    submit_clicked = True
            
            # Console panel
            if st.session_state.get("console_output"):
                st.write("")
                st.markdown("<div class='console-title'>Execution Console</div>", unsafe_allow_html=True)
                is_success = st.session_state.get("console_success", True)
                status_class = "console-success" if is_success else "console-error"
                console_output = html.escape(str(st.session_state.get("console_output") or ""))
                st.markdown(f"<div class='console-pane {status_class}'>{console_output}</div>", unsafe_allow_html=True)

        # Submit answer logic
        if submit_clicked:
            if not user_answer_value or not user_answer_value.strip():
                st.warning("Please provide a response before proceeding.")
            else:
                with st.spinner("Saving your response..."):
                    try:
                        response = requests.post(f"{API_URL}/interview/answer", json={
                            "session_id": session_id,
                            "answer": user_answer_value
                        }, timeout=API_TIMEOUT)
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            if data["is_complete"]:
                                st.session_state["interview_is_complete"] = True
                                st.session_state["final_score"] = data["final_score"]
                            else:
                                st.session_state["current_question_text"] = data["next_question"]
                                st.session_state["current_question_type"] = data.get("question_type", "open_ended")
                                st.session_state["current_options"] = data.get("options")
                                st.session_state["current_initial_code"] = data.get("initial_code")
                                st.session_state["current_topic"] = data.get("current_topic", "background")
                                st.session_state["current_question_number"] = data.get("question_number", 1)
                        else:
                            st.error(_safe_detail(response, "We could not save your response. Please try again."))
                    except requests.exceptions.ConnectionError:
                        st.error("We could not connect to the interview service. Please try again shortly.")
                    except requests.exceptions.Timeout:
                        st.error("The interview service is taking longer than expected. Please try again.")
                    except Exception as e:
                        st.error("We could not save your response. Please try again.")
                st.rerun()

# -----------------------------
# CANDIDATE SIDEBAR (Right Column)
# -----------------------------
with col2:
    st.markdown(
        """
        <div class='side-card-header'>
            <img src='https://cdn-icons-png.flaticon.com/512/9131/9131529.png' width='80'>
            <h4>Assessment Progress</h4>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.write(f"**Candidate:** {name}")
    st.write("**Bootcamp:** Agentic AI")
    
    if is_complete:
        st.success("Status: Completed")
    else:
        st.write(f"**Current stage:** {st.session_state.get('current_topic', 'background').replace('_', ' ').title()}")
        st.write(f"**Question type:** {QUESTION_TYPE_LABELS.get(current_type, current_type.replace('_', ' ').title())}")
        st.info("Status: In Progress")
