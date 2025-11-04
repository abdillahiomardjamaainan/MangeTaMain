# src/streamlit/app/utils.py
from pathlib import Path
import streamlit as st
import yaml

try:
    from src.logging_config import get_logger
    logger = get_logger('mangetamain.streamlit.utils')
except Exception:
    logger = None

from src.data_loader import (
    load_recipes_data,
    load_interactions_data,
    load_clean_recipes,
    load_clean_interactions,
    load_clean_merged,
)

def get_ds():
    """
    ⚠️ Ne charge que les datasets légers au démarrage.
    Les GROS (clean_interactions ~1.1M lignes, merged) seront chargés à la demande.
    """
    if "ds" in st.session_state:
        return st.session_state["ds"]

    if logger: logger.info("Loading datasets via data_loader (light only)")
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

    # LÉGERS
    ds["raw_recipes"]      = _safe("raw_recipes", load_recipes_data)
    ds["raw_interactions"] = _safe("raw_interactions", load_interactions_data)
    ds["clean_recipes"]    = _safe("clean_recipes", load_clean_recipes)

    # GROS — lazy (chargés par boutons dans les pages)
    ds["clean_interactions"] = None
    ds["merged"]             = None

    st.session_state["ds"] = ds
    return ds

# --- commentaires facultatifs pour les viz
def _load_commentary_yaml():
    p = Path(__file__).parent / "comment.yaml"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

_EXPLANATIONS = _load_commentary_yaml()
_MD_MAP = {}

def _get_comment(func_name: str) -> str:
    return _EXPLANATIONS.get(func_name) or _MD_MAP.get(func_name)

# --- Rendu standard des viz
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

    FAST_MODE = st.session_state.get("FAST_MODE", False)
    block = st.expander(label, expanded=not expander) if expander else st.container()

    with block:
        if FAST_MODE and sample_if_fast and hasattr(df, "__len__") and len(df) > sample_if_fast:
            try:
                df = df.sample(sample_if_fast, random_state=42)
            except Exception:
                pass

        try:
            fig = func(df, return_fig=True, **kwargs)
            if fig is None:
                st.info("Figure non retournée par la fonction.")
                return
            st.pyplot(fig, use_container_width=True)

            if show_doc:
                import inspect as _inspect
                doc = _inspect.getdoc(func)
                comment = _get_comment(func.__name__)
                if doc:
                    st.caption(doc)
                if comment:
                    st.markdown(comment)

            if FAST_MODE:
                st.caption("FAST_MODE actif (échantillonnage).")
        except Exception as e:
            st.error(f"Erreur: {e}")
            if logger:
                logger.error(f"Error rendering '{label}' with {func.__name__}: {e}")

def _safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()
