"""Application Streamlit minimale fiable (Accueil + navigation)."""

# --- Bootstrap pour autoriser "from src..." partout ---
import sys
from pathlib import Path
_THIS = Path(__file__).resolve()
for p in [_THIS, *_THIS.parents]:
    if (p / "pyproject.toml").exists():
        for a in (str(p), str(p / "src")):
            if a not in sys.path:
                sys.path.insert(0, a)
        break
# ------------------------------------------------------

import streamlit as st

from src.ensure_data import ensure_data

# Logging
try:
    from src.logging_config import get_logger
    logger = get_logger("mangetamain.streamlit")
except Exception:
    logger = None

# Utils & pages
from src.streamlit.app.utils import get_ds, _safe_rerun
from src.streamlit.app.layouts.page_data_cleaning import show_data_page
from src.streamlit.app.layouts.page_visualisation import show_visualizations
from src.streamlit.app.layouts.page_conclusion import show_conclusion_page


def set_custom_theme(theme="Clair"):
    st.set_page_config(page_title="MangeTaMain", page_icon="🍽️", layout="wide")
    # (thème minimal pour éviter tout souci)
    st.markdown(
        """
        <style>
        .main-header {padding:1rem; border-radius:12px; text-align:center; background:#667eea; color:white;}
        </style>
        """,
        unsafe_allow_html=True,
    )


# ------------------- Page Accueil (TOUT reste DANS la fonction) -------------------
def show_home_page():
    # (debug secrets replié)
    with st.expander("🔍 Debug secrets", expanded=False):
        try:
            st.write("Clés :", list(st.secrets.keys()))
            for k in ["RECIPES_CLEAN_URL","INTERACTIONS_CLEAN_URL","RECIPES_RAW_URL","INTERACTIONS_RAW_URL","MERGED_CLEAN_URL"]:
                ok = k in st.secrets and isinstance(st.secrets[k], str) and st.secrets[k].startswith("http")
                st.write(k, "→", "OK" if ok else "ABSENT/INVALIDE")
        except Exception as e:
            st.write("st.secrets non lisible :", e)

    # >>> NE RIEN SORTIR EN DEHORS DE CETTE FONCTION <<<
    ds = get_ds()
    recipes_df = ds.get("clean_recipes")
    raw_interactions = ds.get("raw_interactions")

    if recipes_df is None or raw_interactions is None:
        st.error("⚠️ Données indisponibles. Vérifie les URLs HF dans Secrets, puis Rerun.")
        st.stop()

    st.markdown('<div class="main-header"><h1>🍽️ MangeTaMain</h1><p>Analyse recettes & interactions</p></div>', unsafe_allow_html=True)
    st.subheader("Aperçu des données")
    st.dataframe(recipes_df.head(5), use_container_width=True)
    st.dataframe(raw_interactions.head(5), use_container_width=True)

    st.markdown("### Navigation rapide")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 Aller à Data cleaning"):
            _set_page_by_key("data"); _safe_rerun()
    with c2:
        if st.button("📈 Aller aux Visualisations"):
            _set_page_by_key("viz"); _safe_rerun()


# -------- Navigation --------
PAGES_ORDER = [
    ("🏠 Accueil", "home", show_home_page),          # ← on passe la fonction, on ne l'appelle pas
    ("📊 Données cleaning", "data", show_data_page),
    ("📈 Visualisations", "viz", show_visualizations),
    ("📝 Conclusion", "conclusion", show_conclusion_page),
]

def _init_page_state():
    if "current_page_idx" not in st.session_state:
        st.session_state.current_page_idx = 0

def _go_delta(delta: int):
    st.session_state.current_page_idx = (st.session_state.current_page_idx + delta) % len(PAGES_ORDER)

def _set_page_by_key(page_key: str):
    for i, (_, key, _) in enumerate(PAGES_ORDER):
        if key == page_key:
            st.session_state.current_page_idx = i
            break


# ------------------- Main -------------------
def main():
    if logger: logger.info("Initializing Streamlit main")
    if "data_ready" not in st.session_state:
        ensure_data(); st.session_state.data_ready = True

    set_custom_theme(st.session_state.get("theme", "Clair"))
    _init_page_state()

    # (log de sanity check – ne déclenche pas d'accès global à ds)
    try:
        _ds = get_ds()
        if logger:
            for k, v in _ds.items():
                if v is not None and hasattr(v, "shape"):
                    logger.debug(f"Dataset {k} shape={v.shape}")
                else:
                    logger.debug(f"Dataset {k} = None")
    except Exception as e:
        if logger: logger.error(f"Load datasets failed: {e}")
        st.error("Erreur chargement des données"); return

    # barre de navigation
    left, center, right = st.columns([1,4,1])
    with left:
        if st.button("◀"): _go_delta(-1); _safe_rerun()
    with center:
        label, key, _ = PAGES_ORDER[st.session_state.current_page_idx]
        st.markdown(f"<h2 style='text-align:center'>{label}</h2>", unsafe_allow_html=True)
    with right:
        if st.button("▶"): _go_delta(1); _safe_rerun()

    with st.sidebar:
        selected = st.radio("Aller à", [lbl for (lbl,_,_) in PAGES_ORDER], index=st.session_state.current_page_idx)
        if PAGES_ORDER[st.session_state.current_page_idx][0] != selected:
            for i, (lbl, key, _) in enumerate(PAGES_ORDER):
                if lbl == selected:
                    st.session_state.current_page_idx = i; _safe_rerun(); break

    # rendu de la page choisie
    _, _, render = PAGES_ORDER[st.session_state.current_page_idx]
    render()


if __name__ == "__main__":
    main()
