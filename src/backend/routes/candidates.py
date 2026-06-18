"""
Candidate Routes - Integrated with Supabase DB & Excel local fallback
"""
import hashlib
import io
import os
import secrets
import smtplib
import sys
from pathlib import Path
from email.message import EmailMessage
from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Ensure project root and src/ are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.append(str(SRC_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from supabase import create_client, Client
from backend.security import create_candidate_token

router = APIRouter(tags=["Candidates"])

# Path to local Excel fallback
EXCEL_PATH = PROJECT_ROOT / "data" / "candidates.xlsx"

# Load environment variables, overriding any pre-existing environment variables
load_dotenv(PROJECT_ROOT / ".env", override=True)

_supabase_url = os.environ.get("SUPABASE_URL")
_supabase_key = os.environ.get("SUPABASE_KEY")
_db_client: Client = None

if _supabase_url and _supabase_key and _supabase_key != "your_supabase_service_role_key_here":
    try:
        _db_client = create_client(_supabase_url, _supabase_key)
        print("Supabase client initialized successfully in candidates router.")
    except Exception as e:
        print(f"Error initializing Supabase client in candidates router: {e}")

# Models
class CandidateVerify(BaseModel):
    email: str

class CandidateCodeVerify(BaseModel):
    email: str
    code: str

class CandidateResponse(BaseModel):
    id: Optional[str] = None
    name: str
    email: str
    position: Optional[str] = None
    status: Optional[str] = None
    score: Optional[float] = None

class CandidateListResponse(BaseModel):
    candidates: List[CandidateResponse]
    total: int
    completed: int
    pending: int
    average_score: float

class CandidateImportError(BaseModel):
    row: int
    errors: List[str]

class CandidateImportResponse(BaseModel):
    success: bool
    inserted: int
    skipped: int
    errors: List[CandidateImportError]
    message: str

_verification_codes: dict[str, dict] = {}
CODE_TTL_MINUTES = int(os.environ.get("CANDIDATE_CODE_TTL_MINUTES", "10"))


def _normalize_email(email: str) -> str:
    return str(email or "").strip().lower()


def _code_secret() -> str:
    return os.environ.get("CANDIDATE_TOKEN_SECRET") or os.environ.get("APP_SECRET_KEY") or "local-dev-candidate-code-secret"


def _hash_code(email: str, code: str) -> str:
    return hashlib.sha256(f"{_normalize_email(email)}:{code}:{_code_secret()}".encode("utf-8")).hexdigest()


def _candidate_match(df: pd.DataFrame, email: str) -> pd.DataFrame:
    if "email" not in df.columns:
        return pd.DataFrame()
    return df[df["email"].astype(str).str.strip().str.lower() == _normalize_email(email)]


def _send_verification_email(email: str, code: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("SMTP_FROM") or smtp_user

    if not (smtp_host and sender):
        print(f"[candidate-verification] Code for {email}: {code}")
        return

    message = EmailMessage()
    message["Subject"] = "Your Interview Agent verification code"
    message["From"] = sender
    message["To"] = email
    message.set_content(
        f"Your Interview Agent verification code is {code}.\n\n"
        f"This code expires in {CODE_TTL_MINUTES} minutes."
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as smtp:
        smtp.starttls()
        if smtp_user and smtp_password:
            smtp.login(smtp_user, smtp_password)
        smtp.send_message(message)


def _issue_verification_code(email: str) -> None:
    normalized = _normalize_email(email)
    code = f"{secrets.randbelow(1_000_000):06d}"
    _verification_codes[normalized] = {
        "code_hash": _hash_code(normalized, code),
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=CODE_TTL_MINUTES),
    }
    _send_verification_email(normalized, code)


def _db_status(value: str) -> str:
    normalized = str(value or "new").strip().lower()
    return normalized if normalized in {"new", "interviewing", "interviewed", "accepted", "rejected"} else "new"

def load_candidates_data() -> pd.DataFrame:
    """Load candidates from Supabase DB, falling back to Excel if not available"""
    if _db_client:
        try:
            res = _db_client.table("candidates").select("*").execute()
            if res.data:
                records = []
                for row in res.data:
                    # Fetch score from reports if available
                    score_val = 0.0
                    try:
                        rep_res = _db_client.table("interview_reports").select("overall_score").eq("candidate_id", row["id"]).limit(1).execute()
                        if rep_res.data:
                            score_val = float(rep_res.data[0]["overall_score"]) * 20.0  # Scale 1-5 to 0-100%
                    except Exception as rep_err:
                        pass
                        
                    records.append({
                        "id": row["id"],
                        "name": row["full_name"],
                        "email": row["email"],
                        "position": row.get("metadata", {}).get("position", "Agentic AI") if row.get("metadata") else "Agentic AI",
                        "status": row["status"].capitalize() if row["status"] else "Pending",
                        "score": score_val
                    })
                return pd.DataFrame(records)
        except Exception as e:
            print(f"Error loading candidates from DB: {e}. Falling back to Excel.")
            
    # Fallback to local Excel file
    if EXCEL_PATH.exists():
        df = pd.read_excel(EXCEL_PATH)
        # Standardize columns
        if "bootcamp" in df.columns and "position" not in df.columns:
            df["position"] = df["bootcamp"]
        if "score" not in df.columns:
            df["score"] = 0.0
        return df
    else:
        # If no excel and no DB, return default mock DataFrame
        return pd.DataFrame([
            {"name": "Ali Ahmed", "email": "ali@example.com", "position": "Agentic AI", "status": "Completed", "score": 95.0},
            {"name": "Sara Hassan", "email": "sara@example.com", "position": "Agentic AI", "status": "Pending", "score": 80.0},
            {"name": "John Doe", "email": "john@example.com", "position": "Agentic AI", "status": "Completed", "score": 97.0},
            {"name": "Mai Salem", "email": "mai@example.com", "position": "Agentic AI", "status": "Completed", "score": 77.0},
            {"name": "Reem Omar", "email": "reem@example.com", "position": "Agentic AI", "status": "Pending", "score": 50.0},
        ])

def save_candidates_data(df):
    """Save candidates back to local Excel fallback"""
    try:
        EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(EXCEL_PATH, index=False)
    except Exception as e:
        print(f"Error saving to Excel fallback: {e}")

@router.post("/candidates/verify")
def verify_candidate(request: CandidateVerify):
    """Verify that the candidate exists and send a short-lived email code."""
    df = load_candidates_data()
    email = _normalize_email(request.email)
    match = _candidate_match(df, email)
    
    if not match.empty:
        candidate_name = match.iloc[0]["name"]
        try:
            _issue_verification_code(email)
        except Exception as exc:
            print(f"Error sending candidate verification email: {exc}")
            raise HTTPException(status_code=500, detail="Could not send verification code. Please try again.")
        return {
            "success": True,
            "name": candidate_name,
            "email": email,
            "verification_required": True,
            "expires_in_minutes": CODE_TTL_MINUTES,
            "message": "Verification code sent to your email."
        }
    raise HTTPException(status_code=404, detail="Email not found. Please contact HR.")


@router.post("/candidates/verify-code")
def verify_candidate_code(request: CandidateCodeVerify):
    """Confirm the email code and issue the signed interview access token."""
    email = _normalize_email(request.email)
    code = str(request.code or "").strip()
    record = _verification_codes.get(email)
    if not record:
        raise HTTPException(status_code=400, detail="No active verification code. Please request a new code.")
    if datetime.now(timezone.utc) > record["expires_at"]:
        _verification_codes.pop(email, None)
        raise HTTPException(status_code=400, detail="Verification code expired. Please request a new code.")
    if not secrets.compare_digest(record["code_hash"], _hash_code(email, code)):
        raise HTTPException(status_code=400, detail="Invalid verification code.")

    df = load_candidates_data()
    match = _candidate_match(df, email)
    if match.empty:
        raise HTTPException(status_code=404, detail="Email not found. Please contact HR.")

    _verification_codes.pop(email, None)
    candidate_name = match.iloc[0]["name"]
    return {
        "success": True,
        "name": candidate_name,
        "email": email,
        "candidate_token": create_candidate_token(email),
        "message": "Email verified successfully."
    }


@router.post("/candidates/resend-code")
def resend_candidate_code(request: CandidateVerify):
    """Resend a candidate verification code if the email exists."""
    return verify_candidate(request)


def _standardize_import_columns(df: pd.DataFrame) -> pd.DataFrame:
    aliases = {
        "full name": "name",
        "fullname": "name",
        "candidate name": "name",
        "student name": "name",
        "e-mail": "email",
        "email address": "email",
        "program": "position",
        "session": "session",
        "bootcamp": "position",
    }
    renamed = {}
    for col in df.columns:
        key = str(col).strip().lower()
        renamed[col] = aliases.get(key, key.replace(" ", "_"))
    return df.rename(columns=renamed)


def _row_errors(row: pd.Series) -> list[str]:
    errors = []
    name = row.get("name")
    if pd.isna(name) or not str(name).strip():
        errors.append("name is required")
    email = _normalize_email(row.get("email"))
    if not email:
        errors.append("email is required")
    elif "@" not in email or "." not in email.split("@")[-1]:
        errors.append("email is invalid")
    return errors


@router.post("/candidates/import-excel", response_model=CandidateImportResponse)
async def import_candidates_excel(file: UploadFile = File(...)):
    """Import recruiter-provided .xlsx candidate rows with row-level validation."""
    if not file.filename.lower().endswith(".xlsx"):
        raise HTTPException(status_code=400, detail="Only .xlsx files are supported.")

    try:
        content = await file.read()
        imported = _standardize_import_columns(pd.read_excel(io.BytesIO(content)))
    except Exception as exc:
        print(f"Error parsing candidate Excel import: {exc}")
        raise HTTPException(status_code=400, detail="Could not parse the Excel file.")

    required = {"name", "email"}
    missing = sorted(required - set(imported.columns))
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    inserted_rows = []
    errors: list[CandidateImportError] = []
    seen_emails: set[str] = set()

    for index, row in imported.iterrows():
        row_number = int(index) + 2
        row_errors = _row_errors(row)
        email = _normalize_email(row.get("email"))
        if email in seen_emails:
            row_errors.append("duplicate email in uploaded file")
        if row_errors:
            errors.append(CandidateImportError(row=row_number, errors=row_errors))
            continue

        seen_emails.add(email)
        name = str(row.get("name")).strip()
        position = str(row.get("position") or row.get("program") or "Agentic AI").strip()
        session = str(row.get("session") or row.get("cohort") or "").strip()
        status = str(row.get("status") or "Pending").strip()
        inserted_rows.append({
            "name": name,
            "email": email,
            "position": position,
            "session": session,
            "status": status,
            "score": 0.0,
        })

        if _db_client:
            try:
                _db_client.table("candidates").upsert({
                    "full_name": name,
                    "email": email,
                    "status": _db_status(status),
                    "metadata": {"position": position, "session": session},
                }, on_conflict="email").execute()
            except Exception as exc:
                errors.append(CandidateImportError(row=row_number, errors=[f"database insert failed: {exc}"]))
                inserted_rows.pop()

    if inserted_rows:
        existing = pd.DataFrame()
        if EXCEL_PATH.exists():
            try:
                existing = pd.read_excel(EXCEL_PATH)
            except Exception:
                existing = pd.DataFrame()
        merged = pd.concat([existing, pd.DataFrame(inserted_rows)], ignore_index=True)
        if "email" in merged.columns:
            merged["email"] = merged["email"].astype(str).str.strip().str.lower()
            merged = merged.drop_duplicates(subset=["email"], keep="last")
        save_candidates_data(merged)

    inserted = len(inserted_rows)
    skipped = len(imported) - inserted
    return CandidateImportResponse(
        success=inserted > 0 and not errors,
        inserted=inserted,
        skipped=skipped,
        errors=errors,
        message=f"Imported {inserted} candidates. {skipped} rows skipped.",
    )

@router.get("/candidates", response_model=CandidateListResponse)
def get_all_candidates():
    """Get all candidates - matches Dashboard.py"""
    df = load_candidates_data()
    
    candidates = []
    for idx, row in df.iterrows():
        candidates.append(CandidateResponse(
            id=str(row.get("id", idx)),
            name=row["name"],
            email=row["email"],
            position=row.get("position", row.get("bootcamp", "Agentic AI")),
            status=row.get("status", "Pending"),
            score=float(row.get("score", 0)) if pd.notna(row.get("score")) else 0.0
        ))
    
    completed = len(df[df["status"].str.lower() == "completed"]) if "status" in df.columns else 0
    pending = len(df[df["status"].str.lower() == "pending"]) if "status" in df.columns else 0
    avg_score = float(df["score"].mean()) if "score" in df.columns and len(df) > 0 else 0.0
    
    return CandidateListResponse(
        candidates=candidates,
        total=len(df),
        completed=completed,
        pending=pending,
        average_score=round(avg_score, 2)
    )

@router.get("/candidates/{candidate_name}")
def get_candidate_by_name(candidate_name: str):
    """Get single candidate by name - matches Reports page"""
    df = load_candidates_data()
    match = df[df["name"] == candidate_name]
    
    if match.empty:
        raise HTTPException(status_code=404, detail="Candidate not found")
    
    row = match.iloc[0]
    return {
        "name": row["name"],
        "email": row["email"],
        "position": row.get("position", row.get("bootcamp", "Agentic AI")),
        "status": row.get("status", "Pending"),
        "score": float(row.get("score", 0)) if pd.notna(row.get("score")) else 0.0
    }

@router.post("/candidates/update-score")
def update_candidate_score(candidate_name: str, score: float):
    """Update candidate's interview score and status after completion"""
    # 1. Update in local Excel first
    try:
        if EXCEL_PATH.exists():
            df = pd.read_excel(EXCEL_PATH)
            if candidate_name in df["name"].values:
                df.loc[df["name"] == candidate_name, "score"] = score
                df.loc[df["name"] == candidate_name, "status"] = "Completed"
                df.loc[df["name"] == candidate_name, "completed_at"] = datetime.now().isoformat()
                df.to_excel(EXCEL_PATH, index=False)
                print(f"Successfully updated candidate score in local Excel for {candidate_name}")
    except Exception as e:
        print(f"Error updating candidate score in local Excel: {e}")
        
    # 2. Update in DB if client is connected
    if _db_client:
        try:
            # Find candidate by name
            res = _db_client.table("candidates").select("id").eq("full_name", candidate_name).execute()
            if res.data:
                cand_id = res.data[0]["id"]
                candidate_status = "accepted" if score >= 80 else ("rejected" if score < 60 else "interviewed")
                _db_client.table("candidates").update({
                    "status": candidate_status,
                }).eq("id", cand_id).execute()
                print(f"Successfully updated candidate status in DB for {candidate_name}")
        except Exception as e:
            print(f"Error updating candidate status in DB: {e}")
            
    return {"success": True, "message": f"Score updated for {candidate_name}"}
