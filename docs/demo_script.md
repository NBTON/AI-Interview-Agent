# Interview Agent Demo Script

## Goal

Show a complete recruiter and candidate workflow without dead ends:

1. Recruiter logs in.
2. Recruiter imports candidates from Excel.
3. Candidate logs in by email.
4. Candidate verifies the emailed code.
5. Candidate completes the interview.
6. Recruiter reviews the final score and report.

## Pre-Demo Setup

1. Use Python 3.12.
2. Install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Create `.env` from `.env.example`.
4. Set:
   ```env
   RECRUITER_EMAIL=demo@example.com
   RECRUITER_PASSWORD=demo-password
   CANDIDATE_TOKEN_SECRET=replace_with_a_long_random_secret
   CANDIDATE_CODE_TTL_MINUTES=10
   ```
5. For a local demo without SMTP, leave `SMTP_HOST` empty. The verification code will print in the backend terminal.
6. Start the backend:
   ```powershell
   uvicorn src.backend.main:app --reload --port 8000
   ```
7. Start the frontend in a second terminal:
   ```powershell
   streamlit run src/frontend/app.py
   ```

## Excel Import File

Prepare a `.xlsx` file with these columns:

| name | email | program | session |
| :--- | :--- | :--- | :--- |
| Demo Candidate | demo.candidate@example.com | Agentic AI | Demo Cohort |

Optional columns: `status`, `phone`, `position`, `bootcamp`.

## Demo Flow

### 1. Recruiter Login

1. Open the Streamlit app.
2. Choose recruiter access.
3. Log in with the configured recruiter credentials.
4. Confirm the dashboard loads with candidate metrics.

### 2. Candidate Import

1. Open the `Candidates` tab.
2. Use `Upload .xlsx file`.
3. Click `Import Candidates`.
4. Confirm the success message shows the inserted row count.
5. If demonstrating validation, upload a file with a blank name or invalid email and show the row-level errors table.

### 3. Candidate Login

1. Return to the home page or open a new browser session.
2. Choose candidate access.
3. Enter the imported candidate email.
4. Click `Send Code`.
5. Read the code from the backend terminal if SMTP is not configured.

### 4. Email Verification

1. Enter the 6-digit code.
2. Click `Verify & Continue`.
3. Confirm the interview page opens.
4. Mention that invalid, expired, or missing codes are blocked and can be resent.

### 5. Interview Flow

1. Answer the first question with a clear background answer.
2. Click `Next Question`.
3. Confirm the UI advances to a new question and topic.
4. Continue answering until completion.
5. For a probe demonstration, give one brief answer such as `I know Python.` and show the targeted follow-up.
6. On the final turn, confirm the thank-you/completion state appears.

### 6. Recruiter Report Review

1. Return to the recruiter dashboard.
2. Open the `Reports` tab.
3. Select the candidate.
4. Review:
   - Final score
   - Recommendation
   - Strengths and weaknesses
   - Question-by-question history
   - Extracted profile data
5. Download the PDF snapshot if needed.

## Recovery Notes

- If candidate verification emails are not arriving, use the backend log code or configure `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`.
- If the interview API returns a persistent checkpoint error, confirm `SUPABASE_DB_URL` or equivalent database settings are configured.
- If import rejects rows, fix the row shown in the validation table and re-upload the `.xlsx` file.
