from pathlib import Path
import streamlit as st
import yaml

# Logging
try:
    from src.logging_config import get_logger
    logger = get_logger('mangetamain.streamlit.utils')
except Exception:
    logger = None

# -------- Chargement via data_loader (local -> sinon URL via st.secrets) --------
from src.data_loader import (
    load_recipes_data,
    load_interactions_data,
    load_clean_recipes,
    load_clean_interactions,
    load_clean_merged,
)

def get_ds():
    """
    Charge tous les datasets via data_loader (local -> sinon URL via st.secrets/env).
    Retourne un dict {name: DataFrame|None}.
    """
    if "ds" in st.session_state:
        return st.session_state["ds"]

    if logger: logger.info("Loading datasets via data_loader")
    ds = {}

    def _safe(name, fn):
        try:
            df = fn()
            if logger:
                shape = getattr(df, "shape", None)
                logger.debug(f"Loaded '{name}': {shape}")
            return df
        except Exception as e:
            msg = f"[utils.get_ds] WARN: '{name}' not loaded: {e}"
            print(msg)
            if logger: logger.warning(msg)
            return None

    ds["raw_recipes"]        = _safe("raw_recipes", load_recipes_data)
    ds["raw_interactions"]   = _safe("raw_interactions", load_interactions_data)
    ds["clean_recipes"]      = _safe("clean_recipes", load_clean_recipes)
    ds["clean_interactions"] = _safe("clean_interactions", load_clean_interactions)
    ds["merged"]             = _safe("merged", load_clean_merged)

    st.session_state["ds"] = ds
    return ds

def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
