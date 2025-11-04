# src/streamlit/app/layouts/page_visualisation.py
import streamlit as st

from src.streamlit.app.utils import get_ds, render_viz
from src.data_loader import load_clean_interactions, load_clean_merged

try:
    from src.data_visualization import (
        rating_distribution,
        recipe_mean_rating_distribution,
        top_users_by_activity,
        user_mean_rating_distribution,
        user_count_vs_mean_rating,
        activity_bucket_bar,
        analyze_contributors,
        statistique_descriptive,
        plot_prep_time_distribution,
        plot_ingredient,
        plot_n_steps_distribution,
        analyse_tags,
        plot_tags_distribution,
        plot_nutrition_distribution,
        analyze_ingredients_vectorized,
        minutes_group_negative_reviews_bar,
        spearman_correlation,
        plot_ingredients_vs_negative_score,
        analyze_tags_correlation,
        nutrition_correlation_analysis,
        get_most_negative_user,
        plot_minutes_ningredients_nsteps,
    )
    DV_OK = True
    DV_ERR = None
except Exception as e:
    DV_OK = False
    DV_ERR = e


def show_visualizations():
    st.markdown("## 📈 Visualisations")

    ds = get_ds()
    df_clean_recipes = ds.get("clean_recipes")

    # --- Chargement lazy des GROS datasets ---
    with st.expander("📥 Charger les gros datasets (à la demande)", expanded=False):
        c1, c2 = st.columns(2)

        with c1:
            if st.button("Charger interactions nettoyées (~1.1M lignes)"):
                dfi = load_clean_interactions()
                if dfi is not None:
                    st.session_state["ds"]["clean_interactions"] = dfi
                    st.success(f"Interactions chargées: {dfi.shape}")
                else:
                    st.error("Impossible de charger interactions_cleaned")

        with c2:
            if st.button("Charger merged_cleaned"):
                dfm = load_clean_merged()
                if dfm is not None:
                    st.session_state["ds"]["merged"] = dfm
                    st.success(f"merged chargé: {dfm.shape}")
                else:
                    st.error("Impossible de charger merged_cleaned")

        cur_i = st.session_state["ds"].get("clean_interactions")
        cur_m = st.session_state["ds"].get("merged")
        st.caption(f"Interactions: {'OK '+str(cur_i.shape) if cur_i is not None else 'Non chargé'}")
        st.caption(f"Merged: {'OK '+str(cur_m.shape) if cur_m is not None else 'Non chargé'}")

    # Récupération après éventuel chargement
    df_interactions = st.session_state["ds"].get("clean_interactions")
    df_merged       = st.session_state["ds"].get("merged")

    # 🔹 Échantillon si énorme
    SAMPLE_MAX = 200_000
    if df_interactions is not None and len(df_interactions) > SAMPLE_MAX:
        st.warning(f"Dataset interactions volumineux → échantillon {SAMPLE_MAX} lignes.")
        df_interactions = df_interactions.sample(SAMPLE_MAX, random_state=42)

    tabs = st.tabs(["Distribution", "Utilisateurs", "Recettes", "Corrélations", "Nutrition"])

    # ---------------- Distribution ----------------
    with tabs[0]:
        if df_interactions is None:
            st.info("Clique sur le bouton ci-dessus pour charger **interactions nettoyées**.")
        else:
            render_viz("Distribution brute des notes", rating_distribution, df_interactions)

        if df_clean_recipes is None:
            st.warning("Recettes nettoyées manquantes (clean_recipes).")
        else:
            render_viz("Analyse des contributeurs des recettes", analyze_contributors, df_clean_recipes)

    # ---------------- Utilisateurs ----------------
    with tabs[1]:
        if df_interactions is None:
            st.info("Charge d’abord **interactions nettoyées**.")
        else:
            render_viz("Top utilisateurs actifs", top_users_by_activity, df_interactions)
            render_viz("Activité (buckets) vs note moyenne", activity_bucket_bar, df_interactions)
            render_viz(
                "Nombre d'avis vs moyenne (échantillon)",
                user_count_vs_mean_rating,
                df_interactions,
                sample_if_fast=2500,  # si ta fonction l'utilise
            )

    # ---------------- Recettes ----------------
    with tabs[2]:
        if df_merged is None:
            st.info("Charge d’abord **merged_cleaned** pour ces graphes.")
        else:
            render_viz("Temps de préparation (catégories)", plot_prep_time_distribution, df_merged)
            render_viz("Nombre d'étapes", plot_n_steps_distribution, df_merged)
            if "tags" in df_merged.columns:
                render_viz("Distribution des tags", plot_tags_distribution, df_merged)

        if df_clean_recipes is not None:
            render_viz("Ingrédients + Pareto", plot_ingredient, df_clean_recipes)

        if df_clean_recipes is not None and st.checkbox("Stats ingrédients vectorisés"):
            try:
                st.dataframe(analyze_ingredients_vectorized(df_clean_recipes))
            except Exception as e:
                st.error(e)

    # ---------------- Corrélations ----------------
    with tabs[3]:
        if df_merged is None:
            st.info("Charge **merged_cleaned** pour voir les corrélations.")
        else:
            render_viz("Minutes vs insatisfaction (groupes)", minutes_group_negative_reviews_bar, df_merged)
            if {"n_ingredients", "negative_reviews"}.issubset(df_merged.columns):
                render_viz("Ingrédients vs insatisfaction", plot_ingredients_vs_negative_score, df_merged)
            if "tags" in df_merged.columns and {"negative_reviews","total_reviews"}.issubset(df_merged.columns):
                render_viz("Tags vs insatisfaction", analyze_tags_correlation, df_merged)

    # ---------------- Nutrition ----------------
    with tabs[4]:
        needed = {"calories","sugar","protein","sodium","total_fat","carbohydrates"}
        if df_merged is None or not needed.issubset(getattr(df_merged, "columns", [])):
            st.warning("Colonnes nutrition manquantes dans `merged`. Charge `merged_cleaned`.")
        else:
            render_viz("Distribution nutrition", plot_nutrition_distribution, df_merged)
            render_viz("Corrélations nutrition ↔ insatisfaction", nutrition_correlation_analysis, df_merged)
