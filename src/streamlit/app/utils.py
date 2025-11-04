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
    Retourne un dict {name: DataFrame|None}. Stocké une fois dans st.session_state["ds"].
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


# --------- (facultatif) commentaires pour les viz ---------
def _load_commentary_yaml():
    p = Path(__file__).parent / "comment.yaml"
    if not p.exists():
        return {}
    try:
        return yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}

_EXPLANATIONS = _load_commentary_yaml()
_MD_MAP = {}  # tu peux ajouter des textes par défaut ici

def _get_comment(func_name: str) -> str:
    return _EXPLANATIONS.get(func_name) or _MD_MAP.get(func_name)


# --------- Rendu standardisé des visualisations ---------
def render_viz(
    label,
    func,
    df,
    show_doc=False,
    expander=True,
    sample_if_fast: int | None = None,
    **kwargs,
):
    """
    Affiche une visualisation en appelant `func(df, return_fig=True, **kwargs)`.
    - Si df est None → warning.
    - Si st.session_state['FAST_MODE'] et sample_if_fast → échantillonne.
    - Affiche docstring + commentaire s'ils existent.
    """
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
