# src/streamlit/app/layouts/page_data_cleaning.py
import streamlit as st
from src.streamlit.app.utils import get_ds, render_viz, _safe_rerun

try:
    from src.data_visualization import plot_minutes_ningredients_nsteps
    from src.preprocessing import (
        detect_missing_values,
        detect_duplicates,
        remove_outliers_nutrition,
        clean_review,
        is_negative_sentence,
        binary_sentiment,
    )
    DV_OK = True
    DV_ERR = None
except Exception as e:
    DV_OK = False
    DV_ERR = e

def show_data_page():
    st.markdown("## 📊 Data cleaning")

    ds = get_ds()
    df_raw_interactions = ds.get("raw_interactions")
    df_raw_recipes      = ds.get("raw_recipes")

    if df_raw_interactions is None or df_raw_recipes is None:
        st.info("Charge d’abord les datasets RAW via la sidebar (boutons).")
        st.stop()

    # Missing (interactions)
    missing_interactions = detect_missing_values(df_raw_interactions)
    missing_df = (
        missing_interactions[missing_interactions > 0]
        .sort_values(ascending=False)
        .to_frame(name="missing")
        .astype(int)
    )
    with st.expander("Valeurs manquantes (interactions)", expanded=False):
        if missing_df.empty:
            st.success("Aucune valeur manquante dans interactions.")
        else:
            st.dataframe(missing_df, width="stretch")

    # Binary sentiment
    df_raw_interactions = df_raw_interactions.copy()
    if "rating" in df_raw_interactions.columns:
        df_raw_interactions["binary_sentiment"] = df_raw_interactions["rating"].apply(
            lambda x: 1 if x in [1, 2, 3] else 0
        )
    st.dataframe(df_raw_interactions.head(5), width="stretch")

    # Recipes — viz boxplots
    render_viz(
        "Boxplots minutes / n_ingredients / n_steps",
        plot_minutes_ningredients_nsteps,
        df_raw_recipes
    )
