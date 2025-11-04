import streamlit as st

from src.streamlit.app.utils import get_ds, render_viz

# Fonctions de visualisation
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


# ---------------------------------------------------------------------------
# Page Visualisations
# ---------------------------------------------------------------------------
def show_visualizations():
    st.markdown("## 📈 Visualisations")

    # — Charger les datasets UNIQUEMENT dans la fonction —
    ds = get_ds()
    df_merged        = ds.get("merged")
    df_interactions  = ds.get("clean_interactions") or ds.get("interactions")
    df_clean_recipes = ds.get("clean_recipes")

    tabs = st.tabs(
        ["Distribution", "Utilisateurs", "Recettes", "Corrélations", "Nutrition"]
    )

    # ---------------------- Onglet Distribution ----------------------
    with tabs[0]:
        if df_interactions is None:
            st.error("⚠️ Interactions manquantes (clean_interactions).")
        else:
            render_viz("Distribution brute des notes", rating_distribution, df_interactions)
            st.markdown(
                """On observe un **biais positif** (concentration sur 4–5)."""
            )

        if df_clean_recipes is None:
            st.warning("Recettes nettoyées manquantes (clean_recipes).")
        else:
            render_viz(
                "Analyse des contributeurs des recettes",
                analyze_contributors,
                df_clean_recipes,
            )
            st.markdown(
                """> Plus de la moitié des contributeurs n’ont qu’**une** recette ; le top 500 produit > 50% du contenu."""
            )

    # ---------------------- Onglet Utilisateurs ----------------------
    with tabs[1]:
        if df_interactions is None:
            st.error("⚠️ Interactions manquantes (clean_interactions).")
        else:
            render_viz("Top utilisateurs actifs", top_users_by_activity, df_interactions)
            render_viz("Activité (buckets) vs note moyenne", activity_bucket_bar, df_interactions)
            # Paramètre 'sample' selon ta signature interne (adaptable)
            render_viz(
                "Nombre d'avis vs moyenne (échantillon)",
                user_count_vs_mean_rating,
                df_interactions,
                sample_if_fast=2500,  # si ta fonction supporte, sinon retire l’arg
            )
            st.markdown(
                """Les utilisateurs très actifs ont une moyenne **élevée** (~4.5–5)."""
            )

    # ---------------------- Onglet Recettes ----------------------
    with tabs[2]:
        # Temps préparation
        if df_merged is not None:
            render_viz(
                "Temps de préparation (catégories)",
                plot_prep_time_distribution,
                df_merged,
            )
            st.markdown(
                """La plupart des recettes <= **2 heures** ; quelques extrêmes très longues existent."""
            )
        else:
            st.warning("Dataset `merged` manquant pour certaines visualisations.")

        # Ingrédients / étapes / tags
        if df_clean_recipes is not None:
            render_viz("Ingrédients + Pareto", plot_ingredient, df_clean_recipes)
        if df_merged is not None:
            render_viz("Nombre d'étapes", plot_n_steps_distribution, df_merged)
            if "tags" in df_merged.columns:
                render_viz("Distribution des tags", plot_tags_distribution, df_merged)
                if st.checkbox("Afficher stats tags"):
                    try:
                        st.dataframe(analyse_tags(df_merged))
                    except Exception as e:
                        st.error(e)
        if df_clean_recipes is not None and st.checkbox("Stats ingrédients vectorisés"):
            try:
                st.dataframe(analyze_ingredients_vectorized(df_clean_recipes))
            except Exception as e:
                st.error(e)

    # ---------------------- Onglet Corrélations ----------------------
    with tabs[3]:
        if df_merged is not None:
            render_viz(
                "Minutes vs insatisfaction (groupes)",
                minutes_group_negative_reviews_bar,
                df_merged,
            )

            if {"n_ingredients", "negative_reviews"}.issubset(df_merged.columns):
                render_viz(
                    "Ingrédients vs insatisfaction",
                    plot_ingredients_vs_negative_score,
                    df_merged,
                )
                st.markdown(
                    """Pas de relation forte entre **durée/complexité** et **insatisfaction**."""
                )

            if "tags" in df_merged.columns and {"negative_reviews","total_reviews"}.issubset(df_merged.columns):
                render_viz("Tags vs insatisfaction", analyze_tags_correlation, df_merged)
        else:
            st.warning("Dataset `merged` manquant pour les corrélations.")

    # ---------------------- Onglet Nutrition ----------------------
    with tabs[4]:
        needed = {"calories","sugar","protein","sodium","total_fat","carbohydrates"}
        if df_merged is None or not needed.issubset(df_merged.columns):
            st.warning("Colonnes nutrition manquantes dans `merged`.")
        else:
            render_viz("Distribution nutrition", plot_nutrition_distribution, df_merged)
            render_viz(
                "Corrélations nutrition ↔ insatisfaction",
                nutrition_correlation_analysis,
                df_merged,
            )
            st.markdown(
                """Les caractéristiques nutritionnelles n’expliquent pas l’insatisfaction."""
            )
