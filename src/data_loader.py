# src/data_loader.py
from __future__ import annotations
from pathlib import Path
from io import BytesIO
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

# --- Chemins locaux (si tu as ces fichiers en local, on les prend d'abord) ---
DATA_DIR = Path(__file__).parent.parent / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"

# Fichiers attendus localement (si présents)
RAW_RECIPES_LOCAL        = RAW_DIR / "RAW_recipes.parquet"
RAW_INTERACTIONS_LOCAL   = RAW_DIR / "RAW_interactions.parquet"
CLEAN_RECIPES_LOCAL      = PROCESSED_DIR / "recipes_cleaned.parquet"
CLEAN_INTERACTIONS_LOCAL = PROCESSED_DIR / "interactions_cleaned.parquet"
CLEAN_MERGED_LOCAL       = PROCESSED_DIR / "merged_cleaned.parquet"

# Clés secrets → URLs Hugging Face (tu les as déjà ajoutées)
SECRET_KEYS = {
    "raw_recipes":        "RECIPES_RAW_URL",
    "raw_interactions":   "INTERACTIONS_RAW_URL",
    "clean_recipes":      "RECIPES_CLEAN_URL",
    "clean_interactions": "INTERACTIONS_CLEAN_URL",
    "merged":             "MERGED_CLEAN_URL",
}

def _log(msg: str):
    if logger:
        logger.info(msg)

# ---------- utilitaires de chargement ----------
def _read_local_any(local_path: Path) -> pd.DataFrame | None:
    """Essaie parquet puis csv si présent localement."""
    try:
        if local_path.suffix.lower() == ".parquet" and local_path.exists():
            return pd.read_parquet(local_path)
        # fallback: si on t’a donné un .csv à la place
        csv_candidate = local_path.with_suffix(".csv")
        if csv_candidate.exists():
            return pd.read_csv(csv_candidate)
    except Exception as e:
        _log(f"Local read failed for {local_path}: {e}")
    return None

def _read_remote_parquet(secret_key: str) -> pd.DataFrame | None:
    """Télécharge un parquet via URL dans st.secrets[secret_key]."""
    url = st.secrets.get(secret_key)
    if not url or not isinstance(url, str):
        _log(f"Secret {secret_key} absent")
        return None
    if requests is None:
        _log("requests non disponible")
        return None
    try:
        _log(f"Téléchargement {secret_key} depuis URL (taille potentiellement élevée)…")
        r = requests.get(url, timeout=600)
        r.raise_for_status()
        bio = BytesIO(r.content)
        return pd.read_parquet(bio)
    except Exception as e:
        _log(f"Echec téléchargement/lecture parquet pour {secret_key}: {e}")
        # fallback CSV si jamais l’URL pointe vers un CSV
        try:
            from io import StringIO
            return pd.read_csv(StringIO(r.content.decode("utf-8")))
        except Exception:
            return None

# ---------- loaders publics (cachés) ----------
@st.cache_data(show_spinner=False)
def load_recipes_data() -> pd.DataFrame | None:
    """RAW_recipes"""
    df = _read_local_any(RAW_RECIPES_LOCAL)
    if df is not None: return df
    return _read_remote_parquet(SECRET_KEYS["raw_recipes"])

@st.cache_data(show_spinner=False)
def load_interactions_data() -> pd.DataFrame | None:
    """RAW_interactions"""
    df = _read_local_any(RAW_INTERACTIONS_LOCAL)
    if df is not None: return df
    return _read_remote_parquet(SECRET_KEYS["raw_interactions"])

@st.cache_data(show_spinner=False)
def load_clean_recipes() -> pd.DataFrame | None:
    """recipes_cleaned"""
    df = _read_local_any(CLEAN_RECIPES_LOCAL)
    if df is not None: return df
    return _read_remote_parquet(SECRET_KEYS["clean_recipes"])

@st.cache_data(show_spinner=False)
def load_clean_interactions() -> pd.DataFrame | None:
    """interactions_cleaned"""
    df = _read_local_any(CLEAN_INTERACTIONS_LOCAL)
    if df is not None: return df
    return _read_remote_parquet(SECRET_KEYS["clean_interactions"])

@st.cache_data(show_spinner=False)
def load_clean_merged() -> pd.DataFrame | None:
    """merged_cleaned"""
    df = _read_local_any(CLEAN_MERGED_LOCAL)
    if df is not None: return df
    return _read_remote_parquet(SECRET_KEYS["merged"])
