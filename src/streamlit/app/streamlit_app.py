# src/streamlit/app/streamlit_app.py
"""Application Streamlit principale (plots + textes explicatifs)."""

from pathlib import Path
import sys
import streamlit as st

# Bootstrap sys.path (projet + src)
_THIS = Path(__file__).resolve()
for p in [_THIS, *_THIS.parents]:
    if (p / "pyproject.toml").exists():
        for a in (str(p), str(p / "src")):
            if a not in sys.path:
                sys.path.insert(0, a)
        break

# Logs
try:
    from src.logging_config import get_logger
    logger = get_logger("mangetamain.streamlit")
    logger.info("Initializing Streamlit main")
except Exception:
    logger = None

# Data ensure (optionnel)
try:
    from src.ensure_data import ensure_data
except Exception:
    def ensure_data():
        pass

# Utils & pages
from src.streamlit.app.utils import get_ds, _safe_rerun
from src.streamlit.app.layouts.page_data_cleaning import show_data_page
from src.streamlit.app.layouts.page_visualisation import show_visualizations
# si tu as une page conclusion, sinon commente :
try:
    from src.streamlit.app.layouts.page_conclusion import show_conclusion_page
except Exception:
    def show_conclusion_page():
        st.info("Conclusion à venir.")

# Loaders (panneau boutons)
from src.data_loader import (
    load_recipes_data,
    load_interactions_data,
    load_clean_recipes,
    load_clean_interactions,
    load_clean_merged,
)

# --------------------- UI helpers ---------------------
def set_custom_theme(theme="Clair"):
    if theme == "Sombre":
        colors = {
            "primary": "#ffffff",
            "secondary": "#f0f0f0",
            "background": "#181a1b",
            "text": "#e0e0e0",
            "header_gradient": "linear-gradient(135deg,#444,#111)",
            "sidebar_gradient": "linear-gradient(180deg,#333,#111)",
            "button_text": "#ffffff",
        }
    else:
        colors = {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "background": "#F0F2F6",
            "text": "#2C3E50",
            "header_gradient": "linear-gradient(135deg,#667eea,#764ba2)",
            "sidebar_gradient": "linear-gradient(180deg,#667eea,#764ba2)",
            "button_text": "#ffffff",
        }
    st.markdown(
        f"""
    <style>
    .stApp {{background:{colors['background']}; color:{colors['text']};}}
    .main-header {{background:{colors['header_gradient']}; padding:1.0rem; border-radius:14px;
                   color:{colors['button_text']} !important; text-align:center; margin-bottom:0.8rem;}}
    [data-testid="stSidebar"] {{background:{colors['sidebar_gradient']};}}
    [data-testid="stSidebar"] * {{color:#ffffff !important;}}
    .stButton>button {{
        background:{colors['header_gradient']}; color:{colors['button_text']} !important;
        border:none; border-radius:24px; padding:0.55rem 1.3rem; font-weight:600;
    }}
    </style>
    """,
        unsafe_allow_html=True,
    )

def data_loader_panel():
    st.markdown("### 📦 Chargement des données (à la demande)")
    ds = get_ds()
    c1, c2, c3 = st.columns(3)

    with c1:
        if st.button("RAW_recipes"):
            df = load_recipes_data()
            if df is not None:
                ds["raw_recipes"] = df
                st.success(f"RAW_recipes: {df.shape}")
            else:
                st.error("RAW_recipes introuvable")

        if st.button("clean_recipes"):
            df = load_clean_recipes()
            if df is not None:
                ds["clean_recipes"] = df
                st.success(f"clean_recipes: {df.shape}")
            else:
                st.error("clean_recipes introuvable")

    with c2:
        if st.button("RAW_interactions"):
            df = load_interactions_data()
            if df is not None:
                ds["raw_interactions"] = df
                st.success(f"RAW_interactions: {df.shape}")
            else:
                st.error("RAW_interactions introuvable")

        if st.button("clean_interactions (gros)"):
            df = load_clean_interactions()
            if df is not None:
                ds["clean_interactions"] = df
                st.success(f"clean_interactions: {df.shape}")
            else:
                st.error("clean_interactions introuvable")

    with c3:
        if st.button("merged_cleaned (gros)"):
            df = load_clean_merged()
            if df is not None:
                ds["merged"] = df
                st.success(f"merged: {df.shape}")
            else:
                st.error("merged introuvable")

    st.caption(
        "État: " +
        ", ".join([f"{k}={'OK' if v is not None else '—'}" for k,v in ds.items()])
    )

# --------------------- Pages ---------------------
def show_home_page():
    st.markdown("## INTRODUCTION")
    st.markdown(
        """Projet **MangeTaMain** — EDA sur recettes et interactions. 
        ⚠️ Pour voir les aperçus, charge d'abord les datasets via la **sidebar**."""
    )
    ds = get_ds()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Aperçu recipes (si chargé)")
        if ds.get("clean_recipes") is not None:
            st.dataframe(ds["clean_recipes"].head(5), width="stretch")
        else:
            st.caption("clean_recipes non chargé.")
    with c2:
        st.markdown("### Aperçu interactions RAW (si chargé)")
        if ds.get("raw_interactions") is not None:
            st.dataframe(ds["raw_interactions"].head(5), width="stretch")
        else:
            st.caption("raw_interactions non chargé.")

PAGES_ORDER = [
    ("🏠 Accueil", "home", show_home_page),
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

# --------------------- Main ---------------------
def main():
    ensure_data()  # no-op si pas utilisé
    st.set_page_config(page_title="MangeTaMain", page_icon="🍽️", layout="wide")
    _init_page_state()

    if "theme" not in st.session_state:
        st.session_state.theme = "Clair"
    set_custom_theme(st.session_state.theme)

    with st.sidebar:
        st.markdown("## Pages")
        selected = st.radio(
            "Aller à",
            [lbl for (lbl, _, _) in PAGES_ORDER],
            index=st.session_state.current_page_idx,
        )
        if PAGES_ORDER[st.session_state.current_page_idx][0] != selected:
            for i, (lbl, key, _) in enumerate(PAGES_ORDER):
                if lbl == selected:
                    st.session_state.current_page_idx = i
                    _safe_rerun()
                    break

        st.selectbox(
            "Thème",
            ["Clair", "Sombre"],
            index=["Clair", "Sombre"].index(st.session_state.theme),
            key="theme_selector",
            on_change=lambda: st.session_state.update(theme=st.session_state.theme_selector),
        )

        st.markdown("---")
        data_loader_panel()

    st.markdown(
        """
        <div class="main-header">
          <h1>🍽️ MangeTaMain</h1>
          <p>Analyse des recettes et interactions</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, key, render = PAGES_ORDER[st.session_state.current_page_idx]
    render()

if __name__ == "__main__":
    main()
