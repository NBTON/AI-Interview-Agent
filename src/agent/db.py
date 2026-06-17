import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote, urlparse

from dotenv import load_dotenv

try:
    from supabase import create_client, Client
except Exception as exc:
    create_client = None
    Client = object
    print(f"Supabase client import unavailable; using local fallback mode: {exc}")


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env", override=True)


def _configured(value: str | None) -> bool:
    return bool(value and value.strip() and not value.startswith("your_"))


@lru_cache(maxsize=1)
def get_supabase_client() -> Client | None:
    """Return the backend Supabase client used by graph nodes and API routes."""
    if not create_client:
        return None

    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not (_configured(url) and _configured(key)):
        return None

    try:
        return create_client(url, key)
    except Exception as exc:
        print(f"Error initializing Supabase client: {exc}")
        return None


def get_postgres_dsn() -> str | None:
    """Direct PostgreSQL DSN for LangGraph PostgresSaver and node-level SQL hooks."""
    for name in ("SUPABASE_DB_URL", "DATABASE_URL", "POSTGRES_URL"):
        value = os.environ.get(name)
        if _configured(value):
            return value

    supabase_url = os.environ.get("SUPABASE_URL")
    db_password = os.environ.get("SUPABASE_DB_PASSWORD")
    if _configured(supabase_url) and _configured(db_password):
        project_ref = urlparse(supabase_url).hostname
        if project_ref:
            project_ref = project_ref.split(".")[0]
            db_host = os.environ.get("SUPABASE_DB_HOST") or f"db.{project_ref}.supabase.co"
            db_name = os.environ.get("SUPABASE_DB_NAME") or "postgres"
            db_user = os.environ.get("SUPABASE_DB_USER") or "postgres"
            encoded_password = quote(db_password, safe="")
            return f"postgresql://{db_user}:{encoded_password}@{db_host}:5432/{db_name}?sslmode=require"
    return None


def require_postgres_dsn() -> str:
    dsn = get_postgres_dsn()
    if not dsn:
        raise RuntimeError(
            "Set SUPABASE_DB_URL, DATABASE_URL, POSTGRES_URL, or SUPABASE_DB_PASSWORD with SUPABASE_URL "
            "to enable persistent LangGraph checkpoints."
        )
    return dsn
