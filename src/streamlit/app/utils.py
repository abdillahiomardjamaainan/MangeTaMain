# src/streamlit/app/utils.py
from pathlib import Path
import streamlit as st
import yaml

try:
    from src.logging_config import get_logger
    logger = get_logger('mangetamain.streamlit.utils')
except Exception:
    logger = None

# --------- Ultra-lazy store (rien au boot) ----------
def get_ds():
    """
    Ultra-lazy: ne PRÉCHARGE rien au démarrage.
    Tous les datasets restent à None et seront chargés par des boutons dans les pages.
    """
    if "ds" in st.session_state:
        return st.session_state["ds"]

    st.session_state["ds"] = {
        "raw_recipes": None,
        "raw_interactions": None,
        "clean_recipes": None,
        "clean_interactions": None,
        "merged": None,
    }
    return st.session_state["ds"]

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
            st.pyplot(fig, width="stretch")

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

# --- Sampling utils ----------------------------------------------------------
def get_sample(df, n: int, seed: int):
    """Retourne un échantillon de n lignes (ou moins si n > len(df)).
    Si df est None, retourne None."""
    if df is None:
        return None
    n = int(max(1, min(n, len(df))))
    if n >= len(df):
        return df
    return df.sample(n, random_state=seed)

def sample_controls(key_prefix: str, default_n: int = 50_000, max_n: int | None = None):
    """Panneau Streamlit pour choisir taille d'échantillon + resampler.
    Renvoie (sample_size, seed, asked_rerun: bool)"""
    if "sample_seed" not in st.session_state:
        st.session_state.sample_seed = 0

    max_n = max_n or 200_000

    with st.expander("⚙️ Contrôles d'échantillonnage", expanded=False):
        col1, col2, col3 = st.columns([2,2,1])
        with col1:
            n = st.slider("Taille d'échantillon", 1_000, max_n, value=default_n, step=1_000, key=f"{key_prefix}_n")
        with col2:
            st.caption(f"Seed actuel : {st.session_state.sample_seed}")
        with col3:
            resample = st.button("🎲 Nouveau tirage", key=f"{key_prefix}_resample")

        if resample:
            st.session_state.sample_seed += 1
            _safe_rerun()

    return st.session_state.get(f"{key_prefix}_n", default_n), st.session_state.sample_seed, False
