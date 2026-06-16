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
 
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500;700&display=swap');
 
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
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
 
[data-testid="stHeader"] { background: transparent !important; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 1.25rem !important; }
 
/* Question panel — matches app.py custom-card */
.question-panel {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 22px;
    padding: 30px 34px;
    border: 1px solid rgba(143, 164, 190, 0.1);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    margin: 8px 0 24px;
    animation: fadeIn 0.6s ease-out;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
.question-panel:hover {
    box-shadow: 0 32px 70px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(0, 201, 167, 0.2);
    border-color: rgba(0, 201, 167, 0.18);
}
 
.question-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid rgba(143, 164, 190, 0.1);
}
 
.question-type {
    font-size: 11px;
    font-weight: 700;
    color: #8FA4BE;
    text-transform: uppercase;
    letter-spacing: 1.2px;
}
 
.question-topic {
    background: rgba(0, 201, 167, 0.1);
    color: #00C9A7;
    padding: 5px 14px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    border: 1px solid rgba(0, 201, 167, 0.22);
}
 
.question-prompt {
    font-family: 'Outfit', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #E8EDF3;
    line-height: 1.55;
    margin-top: 6px;
    margin-bottom: 22px;
    letter-spacing: -0.2px;
}
 
/* Text area */
div[data-testid="stTextArea"] label,
div[data-testid="stTextArea"] label p { color: #8FA4BE !important; font-size: 13px !important; font-weight: 500 !important; }
div[data-testid="stTextArea"] textarea {
    background: rgba(10, 22, 40, 0.75) !important;
    border: 1px solid rgba(143, 164, 190, 0.2) !important;
    border-radius: 12px !important;
    color: #E8EDF3 !important;
    font-size: 15px !important;
    font-family: 'Inter', sans-serif !important;
    transition: border-color 0.2s ease !important;
}
div[data-testid="stTextArea"] textarea:focus {
    border-color: #00C9A7 !important;
    box-shadow: 0 0 0 3px rgba(0, 201, 167, 0.1) !important;
}
 
/* Radio options */
div[data-testid="stRadio"] label,
div[role="radiogroup"] label {
    background: rgba(22, 34, 54, 0.7) !important;
    border: 1px solid rgba(143, 164, 190, 0.12) !important;
    border-radius: 12px !important;
    padding: 12px 18px !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    color: #C8D8E8 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
    font-family: 'Inter', sans-serif !important;
}
div[data-testid="stRadio"] label:hover,
div[role="radiogroup"] label:hover {
    background: rgba(0, 201, 167, 0.06) !important;
    border-color: rgba(0, 201, 167, 0.3) !important;
    transform: translateX(4px) !important;
    color: #00C9A7 !important;
}
div[data-testid="stRadio"] label[data-checked="true"],
div[role="radiogroup"] label[data-checked="true"] {
    background: rgba(0, 201, 167, 0.1) !important;
    border-color: #00C9A7 !important;
    color: #00C9A7 !important;
}
div[data-testid="stRadio"] div[role="radiogroup"] { flex-wrap: wrap !important; gap: 10px !important; }
 
/* IDE shell */
.ide-shell {
    background: #060C16;
    border: 1px solid rgba(143, 164, 190, 0.1);
    border-bottom: none;
    border-radius: 14px 14px 0 0;
    margin-top: 4px;
}
.ide-titlebar {
    height: 40px;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: #4A6280;
}
.ide-dot { width: 11px; height: 11px; border-radius: 999px; display: inline-block; }
.ide-dot.red    { background: #EF4444; }
.ide-dot.yellow { background: #FFB547; }
.ide-dot.green  { background: #00C9A7; }
.ide-filename { margin-left: 8px; color: #4A6280; font-size: 12px; }
 
div[data-testid="stTextArea"] textarea[aria-label="Code editor"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    line-height: 1.65 !important;
    background: #060C16 !important;
    color: #C8D8E8 !important;
    border-radius: 0 0 14px 14px !important;
    padding: 18px !important;
    border: 1px solid rgba(143, 164, 190, 0.1) !important;
    box-shadow: inset 54px 0 0 #0A1220 !important;
    tab-size: 4;
}
 
/* Console */
.console-title {
    color: #00C9A7;
    font-family: 'JetBrains Mono', monospace;
    font-weight: 700;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin-bottom: 8px;
}
.console-pane {
    background: #060C16;
    color: #8FA4BE;
    padding: 14px 20px;
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    margin-top: 12px;
    border: 1px solid rgba(143, 164, 190, 0.1);
    max-height: 180px;
    overflow-y: auto;
    white-space: pre-wrap;
}
.console-success { color: #00C9A7; }
.console-error   { color: #FF6B6B; }
 
/* Side card — matches custom-card from app.py */
.side-card-header {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    padding: 32px 22px;
    border-radius: 22px;
    border: 1px solid rgba(143, 164, 190, 0.1);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    text-align: center;
    margin-bottom: 16px;
    animation: fadeIn 0.7s ease-out;
}
.side-card-header img { filter: drop-shadow(0 8px 20px rgba(0, 201, 167, 0.18)); }
.side-card-header h4 {
    font-family: 'Outfit', sans-serif;
    color: #E8EDF3;
    font-weight: 800;
    font-size: 17px;
    margin-top: 14px;
    margin-bottom: 16px;
    letter-spacing: -0.2px;
}
 
/* Thank you card */
.thank-you-card {
    background: rgba(22, 34, 54, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 22px;
    padding: 56px 48px;
    border: 1px solid rgba(0, 201, 167, 0.18);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.04);
    text-align: center;
    max-width: 620px;
    margin: 40px auto;
    animation: fadeIn 0.8s ease-out;
}
.thank-you-title {
    font-family: 'Outfit', sans-serif;
    font-size: 36px;
    font-weight: 900;
    color: #00C9A7;
    margin-top: 20px;
    margin-bottom: 16px;
    letter-spacing: -0.5px;
}
.thank-you-text {
    font-size: 16px;
    color: #8FA4BE;
    line-height: 1.65;
    margin-bottom: 32px;
}
 
/* Shared button style */
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
 
/* Streamlit native element overrides */
div[data-testid="stAlert"] { border-radius: 12px !important; }
div[data-testid="stTextInput"] > div > div > input {
    background: rgba(10, 22, 40, 0.75) !important;
    border: 1px solid rgba(143, 164, 190, 0.2) !important;
    border-radius: 12px !important;
    color: #E8EDF3 !important;
}
p, span, [data-testid="stMarkdownContainer"] p { color: #C8D8E8; }
strong { color: #E8EDF3 !important; }
</style>
""", unsafe_allow_html=True)
 
# -----------------------------
# Logic unchanged below
# -----------------------------
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
 
if current_type == "coding":
    if "last_q_number" not in st.session_state:
        st.session_state["last_q_number"] = 0
    if current_number != st.session_state["last_q_number"]:
        st.session_state["user_code_input"] = st.session_state.get("current_initial_code", "")
        st.session_state["last_q_number"] = current_number
        st.session_state["console_output"] = ""
        st.session_state["console_success"] = None
 
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
 
col1, col2 = st.columns([3, 1])
 
# -----------------------------
# QUESTIONNAIRE PANEL
# -----------------------------
with col1:
    if is_complete:
        st.markdown(
            """
            <div class='thank-you-card'>
                <img src='https://cdn-icons-png.flaticon.com/512/190/190411.png' width='100'
                     style='filter: drop-shadow(0 8px 20px rgba(0,201,167,0.25));'>
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
        _, btn_col, _ = st.columns([1, 1, 1])
        with btn_col:
            if st.button("Return to Home 🏠"):
                st.session_state.clear()
                st.switch_page("app.py")
    else:
        topic_raw = st.session_state.get("current_topic", "General")
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
 
        submit_clicked = False
        user_answer_value = ""
        answer_key = f"{session_id}_{current_number}_{current_type}"
 
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
                "1 - Strongly Disagree", "2 - Disagree", "3 - Neutral", "4 - Agree", "5 - Strongly Agree"
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
            if st.session_state.get("console_output"):
                st.write("")
                st.markdown("<div class='console-title'>⬡ Execution Console</div>", unsafe_allow_html=True)
                is_success = st.session_state.get("console_success", True)
                status_class = "console-success" if is_success else "console-error"
                console_output = html.escape(str(st.session_state.get("console_output") or ""))
                st.markdown(f"<div class='console-pane {status_class}'>{console_output}</div>", unsafe_allow_html=True)
 
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
# CANDIDATE SIDEBAR
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