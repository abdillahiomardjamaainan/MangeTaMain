# src/data_loader.py
from __future__ import annotations
from pathlib import Path
from io import BytesIO, StringIO
import pandas as pd
import streamlit as st

try:
    import requests
except Exception:
    requests = None

# Logging (optionnel)
try:
    from src.logging_config import get_logger
    logger = get_logger("data_loader")
except Exception:
    logger = None

def _log(msg: str):
    if logger:
        logger.info(msg)

# --- Chemins locaux (prioritaires s'ils existent) ---
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

RAW_RECIPES_LOCAL        = RAW_DIR / "RAW_recipes.parquet"
RAW_INTERACTIONS_LOCAL   = RAW_DIR / "RAW_interactions.parquet"
CLEAN_RECIPES_LOCAL      = PROCESSED_DIR / "recipes_cleaned.parquet"
CLEAN_INTERACTIONS_LOCAL = PROCESSED_DIR / "interactions_cleaned.parquet"
CLEAN_MERGED_LOCAL       = PROCESSED_DIR / "merged_cleaned.parquet"

# Clés secrets Hugging Face
SECRET_KEYS = {
    "raw_recipes":        "RECIPES_RAW_URL",
    "raw_interactions":   "INTERACTIONS_RAW_URL",
    "clean_recipes":      "RECIPES_CLEAN_URL",
    "clean_interactions": "INTERACTIONS_CLEAN_URL",
    "merged":             "MERGED_CLEAN_URL",
}

def _read_local_any(parquet_path: Path) -> pd.DataFrame | None:
    """Essaie parquet, sinon CSV avec le même nom."""
    try:
        if parquet_path.exists():
            return pd.read_parquet(parquet_path)
        csv_candidate = parquet_path.with_suffix(".csv")
        if csv_candidate.exists():
            return pd.read_csv(csv_candidate)
    except Exception as e:
        _log(f"Local read failed for {parquet_path}: {e}")
    return None

def _read_remote_any(secret_key: str) -> pd.DataFrame | None:
    """
    Charge un fichier distant depuis st.secrets[secret_key].
    Stratégie:
      1) pd.read_parquet(url) direct (pyarrow sait gérer HTTP)
      2) requests.get + BytesIO + read_parquet
      3) fallback CSV (si le lien pointe en réalité vers un CSV)
    """
    url = st.secrets.get(secret_key)
    if not url or not isinstance(url, str):
        _log(f"Secret {secret_key} absent/invalid")
        return None

    # 1) tentative directe
    try:
        _log(f"[{secret_key}] read_parquet direct: {url}")
        return pd.read_parquet(url)
    except Exception as e1:
        _log(f"[{secret_key}] direct read_parquet failed: {e1}")

    # 2) via requests (si disponible)
    if requests is not None:
        try:
            _log(f"[{secret_key}] GET via requests…")
            r = requests.get(url, timeout=600, allow_redirects=True)
            r.raise_for_status()
            bio = BytesIO(r.content)
            try:
                return pd.read_parquet(bio)
            except Exception as e2:
                _log(f"[{secret_key}] parquet via BytesIO failed: {e2}")
                # 3) fallback CSV
                try:
                    return pd.read_csv(StringIO(r.content.decode("utf-8")))
                except Exception as e3:
                    _log(f"[{secret_key}] CSV fallback failed: {e3}")
        except Exception as e:
            _log(f"[{secret_key}] HTTP error: {e}")
    else:
        _log("requests non disponible")

    return None

# ---------- Loaders publics (cachés) ----------
@st.cache_data(show_spinner=False)
def load_recipes_data() -> pd.DataFrame | None:
    df = _read_local_any(RAW_RECIPES_LOCAL)
    return df if df is not None else _read_remote_any(SECRET_KEYS["raw_recipes"])

@st.cache_data(show_spinner=False)
def load_interactions_data() -> pd.DataFrame | None:
    df = _read_local_any(RAW_INTERACTIONS_LOCAL)
    return df if df is not None else _read_remote_any(SECRET_KEYS["raw_interactions"])

@st.cache_data(show_spinner=False)
def load_clean_recipes() -> pd.DataFrame | None:
    df = _read_local_any(CLEAN_RECIPES_LOCAL)
    return df if df is not None else _read_remote_any(SECRET_KEYS["clean_recipes"])

@st.cache_data(show_spinner=False)
def load_clean_interactions() -> pd.DataFrame | None:
    df = _read_local_any(CLEAN_INTERACTIONS_LOCAL)
    return df if df is not None else _read_remote_any(SECRET_KEYS["clean_interactions"])

@st.cache_data(show_spinner=False)
def load_clean_merged() -> pd.DataFrame | None:
    df = _read_local_any(CLEAN_MERGED_LOCAL)
    return df if df is not None else _read_remote_any(SECRET_KEYS["merged"])
