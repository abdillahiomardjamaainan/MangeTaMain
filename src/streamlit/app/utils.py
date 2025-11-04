from pathlib import Path
import sys, inspect
import streamlit as st
import pandas as pd
import yaml

# Logging
try:
    from src.logging_config import get_logger
    logger = get_logger('mangetamain.streamlit.utils')
except Exception as e:
    print(f"Warning: Could not initialize logging in utils: {e}")
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
    if logger:
        logger.info("Loading all datasets for Streamlit application")

    ds = {}

    def _safe(name, fn):
        try:
            df = fn()
            if logger:
                logger.debug(f"Loaded '{name}': {getattr(df, 'shape', None)}")
            return df
        except Exception as e:
            msg = f"[utils.get_ds] WARN: '{name}' not loaded: {e}"
            print(msg)
            if logger:
                logger.warning(msg)
            return None

    ds["raw_recipes"]        = _safe("raw_recipes", load_recipes_data)
    ds["raw_interactions"]   = _safe("raw_interactions", load_interactions_data)
    ds["clean_recipes"]      = _safe("clean_recipes", load_clean_recipes)
    ds["clean_interactions"] = _safe("clean_interactions", load_clean_interactions)
    ds["merged"]             = _safe("merged", load_clean_merged)

    return ds

# -------- Rendu de visualisations --------
def load_commentary_yaml():
    p = Path(__file__).parent / "comment.yaml"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

EXTERNAL_COMMENTS = load_commentary_yaml()
MD_MAP = {}

FAST_MODE = st.session_state.get("FAST_MODE", False)

def get_comment(func_name: str) -> str:
    return EXTERNAL_COMMENTS.get(func_name) or MD_MAP.get(func_name)

def render_viz(
    label,
    func,
    df,
    show_doc=False,
    expander=True,
    sample_if_fast: int | None = None,
    **kwargs,
):
    if df is None:
        st.warning(f"{label}: dataset manquant")
        if logger:
            logger.warning(f"Visualization '{label}' skipped: dataset is None")
        return

    block = st.expander(label, expanded=not expander) if expander else st.container()
    with block:
        if FAST_MODE and sample_if_fast and len(df) > sample_if_fast:
            df = df.sample(sample_if_fast, random_state=42)
        try:
            fig = func(df, return_fig=True, **kwargs)
            if fig is None:
                st.info("Figure non retournée.")
                return
            st.pyplot(fig, use_container_width=True)

            if show_doc:
                import inspect as _inspect
                doc = _inspect.getdoc(func)
                comment = get_comment(func.__name__)
                if doc or comment:
                    if doc:
                        st.caption(doc)
                    if comment:
                        st.markdown(comment)
            if FAST_MODE:
                st.caption("FAST_MODE actif (échantillonnage).")
        except Exception as e:
            st.error(f"Erreur: {e}")

def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
