# Premium CSS stylesheet definitions for AI Interview Platform
# Contains Outfit and JetBrains Mono Google Fonts import and styles

Candidate_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', sans-serif !important;
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%) !important;
    background-size: 400% 400% !important;
    animation: gradientMove 15s ease infinite !important;
}

@keyframes gradientMove {
    0% {background-position: 0% 50%;}
    50% {background-position: 100% 50%;}
    100% {background-position: 0% 50%;}
}

.verify-card {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-radius: 24px;
    padding: 40px;
    border: 1px solid rgba(99, 102, 241, 0.25);
    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
    margin: 20px auto;
    max-width: 500px;
    transition: all 0.3s ease;
}

.verify-card:hover {
    box-shadow: 0 30px 60px rgba(79, 70, 229, 0.15);
    border-color: rgba(99, 102, 241, 0.5);
}

.verify-title {
    text-align: center;
    font-size: 32px;
    font-weight: 800;
    background: linear-gradient(90deg, #4F46E5, #6366F1, #8B5CF6);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
    letter-spacing: -0.5px;
}

.verify-sub {
    text-align: center;
    color: #4B5563;
    font-size: 16px;
    margin-bottom: 30px;
    font-weight: 400;
}

.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1.5px solid rgba(99, 102, 241, 0.2) !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
    background-color: rgba(255, 255, 255, 0.8) !important;
    transition: all 0.2s ease !important;
}

.stTextInput > div > div > input:focus {
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.2) !important;
}

.stButton button {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
    color: white !important;
    border-radius: 14px !important;
    height: 52px !important;
    width: 100% !important;
    border: none !important;
    font-weight: 700 !important;
    font-size: 16px !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.3) !important;
}

.stButton button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(79, 70, 229, 0.45) !important;
    background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%) !important;
}

.stButton button:active {
    transform: translateY(0px) !important;
}
</style>
"""

Chatbot_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: 'Outfit', sans-serif !important;
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%) !important;
    background-size: 400% 400% !important;
    animation: gradientMove 15s ease infinite !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* Questionnaire premium card container */
.questionnaire-card {
    background: rgba(255, 255, 255, 0.82);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 28px;
    padding: 35px 40px;
    border: 1px solid rgba(99, 102, 241, 0.22);
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.05);
    margin-top: 10px;
    margin-bottom: 25px;
    transition: all 0.3s ease;
}

.question-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 1.5px solid rgba(99, 102, 241, 0.15);
}

.question-num {
    font-size: 15px;
    font-weight: 700;
    color: #4B5563;
}

.question-topic {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%);
    color: white;
    padding: 6px 14px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    box-shadow: 0 4px 10px rgba(79, 70, 229, 0.15);
}

.question-prompt {
    font-size: 21px;
    font-weight: 700;
    color: #1E1B4B;
    line-height: 1.5;
    margin-top: 10px;
    margin-bottom: 25px;
}

/* Custom premium styling for MCQ and True/False radio cards */
div[data-testid="stRadio"] label, div[role="radiogroup"] label {
    background: white !important;
    border: 1.5px solid rgba(99, 102, 241, 0.12) !important;
    border-radius: 12px !important;
    padding: 12px 18px !important;
    font-size: 15.5px !important;
    font-weight: 500 !important;
    color: #374151 !important;
    cursor: pointer !important;
    transition: all 0.2s ease !important;
    margin-bottom: 8px !important;
    width: 100% !important;
    display: flex !important;
    align-items: center !important;
}

div[data-testid="stRadio"] label:hover, div[role="radiogroup"] label:hover {
    background: #EEF2FF !important;
    border-color: #6366F1 !important;
    transform: translateX(4px) !important;
}

/* Checked state helper (Streamlit CSS targeting) */
div[data-testid="stRadio"] label[data-checked="true"], div[role="radiogroup"] label[data-checked="true"] {
    background: #E0E7FF !important;
    border-color: #4F46E5 !important;
    box-shadow: 0 0 0 1px #4F46E5 !important;
}

/* Horizontal Radio Adjustments */
div[data-testid="stRadio"] div[role="radiogroup"] {
    flex-wrap: wrap !important;
    gap: 10px !important;
}

/* Monospace IDE Editor styling */
textarea[aria-label="Write/Fix Python Code:"] {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14.5px !important;
    line-height: 1.6 !important;
    background-color: #1E1E2E !important;
    color: #CDD6F4 !important;
    border-radius: 12px !important;
    padding: 16px !important;
    border: 1px solid #313244 !important;
}

.console-pane {
    background: #181825;
    color: #BAC2DE;
    padding: 15px 20px;
    border-radius: 12px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    margin-top: 15px;
    border: 1px solid #313244;
    max-height: 180px;
    overflow-y: auto;
    white-space: pre-wrap;
}

.console-title {
    color: #89B4FA;
    font-weight: 700;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 6px;
}

.console-success {
    color: #A6E3A1;
}

.console-error {
    color: #F38BA8;
}

/* Candidate Information Sidebar panel */
.side-card {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 30px 20px;
    border-radius: 24px;
    border: 1px solid rgba(99, 102, 241, 0.2);
    text-align: center;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.04);
}

.side-card h4 {
    color: #1E1B4B;
    font-weight: 850;
    font-size: 19px;
    margin-top: 15px;
    margin-bottom: 20px;
}

/* Thank You screen container */
.thank-you-card {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: 28px;
    padding: 50px 40px;
    border: 1px solid rgba(16, 185, 129, 0.25);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.06);
    text-align: center;
    max-width: 600px;
    margin: 40px auto;
    animation: fadeIn 0.8s ease-out;
}

.thank-you-title {
    font-size: 32px;
    font-weight: 900;
    background: linear-gradient(90deg, #10B981, #059669);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-top: 20px;
    margin-bottom: 15px;
}

.thank-you-text {
    font-size: 16px;
    color: #4B5563;
    line-height: 1.6;
    margin-bottom: 30px;
}

/* Align inputs and buttons globally */
.stTextInput > div > div > input {
    border-radius: 12px !important;
    border: 1.5px solid rgba(99, 102, 241, 0.2) !important;
    padding: 12px 16px !important;
    font-size: 16px !important;
}

div.stButton > button {
    background: linear-gradient(135deg, #4F46E5 0%, #6366F1 100%) !important;
    color: white !important;
    font-weight: 700 !important;
    padding: 14px 28px !important;
    border-radius: 14px !important;
    border: none !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(79, 70, 229, 0.25) !important;
    font-size: 16px !important;
    width: 100% !important;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #4338CA 0%, #4F46E5 100%) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 22px rgba(79, 70, 229, 0.4) !important;
}

div.stButton > button:active {
    transform: translateY(0px) !important;
}
</style>
"""

Dashboard_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Outfit', sans-serif !important;
    background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 50%, #C7D2FE 100%) !important;
}

.nav-container {
    display: flex;
    gap: 15px;
    margin-bottom: 30px;
    background: rgba(255, 255, 255, 0.5);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    padding: 12px;
    border-radius: 20px;
    border: 1px solid rgba(99, 102, 241, 0.15);
}

/* Custom Navigation Button Styling */
div[data-testid="stHorizontalBlock"] div.stButton > button {
    background: transparent !important;
    color: #4F46E5 !important;
    border: 1.5px solid #4F46E5 !important;
    border-radius: 12px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    box-shadow: none !important;
    transition: all 0.2s ease !important;
    width: 100% !important;
}

div[data-testid="stHorizontalBlock"] div.stButton > button:hover {
    background: rgba(79, 70, 229, 0.08) !important;
    transform: translateY(-1px) !important;
}

.section-box {
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 35px;
    border-radius: 26px;
    border: 1px solid rgba(99, 102, 241, 0.2);
    box-shadow: 0 15px 35px rgba(0, 0, 0, 0.05);
    margin-bottom: 25px;
}

.metric-card {
    background: white;
    padding: 24px;
    border-radius: 20px;
    text-align: center;
    border: 1px solid rgba(99, 102, 241, 0.15);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.03);
    transition: all 0.3s ease;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 15px 30px rgba(79, 70, 229, 0.15);
    border-color: rgba(99, 102, 241, 0.4);
}

.metric-title {
    color: #4B5563;
    font-size: 14px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 6px;
}

.metric-value {
    color: #1E1B4B;
    font-size: 28px;
    font-weight: 800;
}
</style>
"""

Recruiter_Login_CSS = Candidate_CSS
