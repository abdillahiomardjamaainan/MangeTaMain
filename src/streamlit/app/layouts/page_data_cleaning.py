import streamlit as st

try:
    from src.data_visualization import (
        plot_minutes_ningredients_nsteps,
    )
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

from src.streamlit.app.utils import get_ds, _safe_rerun, render_viz


# ---------------------------------------------------------------------------
# Page Data cleaning
# ---------------------------------------------------------------------------
def show_data_page():
    st.markdown("## 📊 Données cleaning")

    # — Charger les datasets UNIQUEMENT dans la fonction —
    ds = get_ds()
    df_raw_interactions   = ds.get("raw_interactions")
    df_raw_recipes        = ds.get("raw_recipes")
    df_clean_recipes      = ds.get("clean_recipes")
    df_clean_interactions = ds.get("clean_interactions")

    if df_raw_interactions is None or df_raw_recipes is None:
        st.error("⚠️ Données RAW manquantes. Vérifie les URLs dans les secrets.")
        st.stop()

    # -------------------- Interactions (RAW) --------------------
    st.markdown("### Data cleaning — **table interactions (RAW)**")

    st.markdown(
        """Il est primordial de nettoyer les données avant toute analyse.
Commençons par les **valeurs manquantes** :"""
    )

    missing_interactions = detect_missing_values(df_raw_interactions)
    missing_df = (
        missing_interactions[missing_interactions > 0]
        .sort_values(ascending=False)
        .to_frame(name="missing")
        .astype(int)
    )

    if missing_df.empty:
        st.success("✅ Aucune valeur manquante détectée dans *interactions*.")
    else:
        with st.expander("🔎 Nombre de valeurs manquantes", expanded=False):
            for col, val in missing_df["missing"].items():
                st.write(f"{col}: {val}")

    st.markdown(
        """### Imputation textuelle pour `review`
- `rating = 5` → "Excellent recipe! Loved it!"  
- `rating = 4` → "Great recipe, will make again."  
- `rating = 3` → "Good recipe, but could be improved."  
- `rating = 2` → "Not my favorite."  
- `rating = 1` → "Did not like this recipe at all."  

La proportion de valeurs manquantes est ~0.01%, cette imputation n'impacte pas l’analyse globale.
"""
    )

    st.markdown("### Traitement de la colonne `rating`")

    st.markdown(
        """Des **ratings = 0** existent alors que l’échelle valide est **1–5**.
Nous considérons **0 comme une absence de note** → on remplace par `NaN` pour ne pas biaiser les statistiques."""
    )

    # --- BINARY SENTIMENT (1 si rating ≤ 3) ---
    st.markdown("### Création de `binary_sentiment` (rating ≤ 3 → 1, sinon 0)")
    df_raw_interactions["binary_sentiment"] = df_raw_interactions["rating"].apply(
        lambda x: 1 if x in [1, 2, 3] else 0
    )

    # Seed échantillon dans session_state
    if "binary_sample_seed" not in st.session_state:
        st.session_state.binary_sample_seed = 0

    interactions_binary_sentiment = st.multiselect(
        "Colonnes à afficher (interactions)",
        df_raw_interactions.columns.tolist(),
        default=df_raw_interactions.columns.tolist()[:8],
    )

    # Échantillon stable (tant que seed inchangé)
    sample_df = df_raw_interactions[interactions_binary_sentiment].sample(
        min(5, len(df_raw_interactions)),
        random_state=st.session_state.binary_sample_seed,
    )
    st.dataframe(sample_df, use_container_width=True)

    col_btn, col_info = st.columns([1, 3])
    with col_btn:
        if st.button("🔄 Rafraîchir échantillon"):
            st.session_state.binary_sample_seed += 1
            _safe_rerun()
    with col_info:
        st.caption(f"Seed échantillon: {st.session_state.binary_sample_seed}")

    st.markdown(
        """Les avis avec un `rating` de **1 à 3** ont bien un `binary_sentiment = 1`.
Pour `rating = 0` (absence de note) et `rating = 4`, on analysera le texte pour détecter des **aspects négatifs**."""
    )

    # -------------------- Recipes (RAW) --------------------
    st.markdown("### Data cleaning — **table recipes (RAW)**")

    missing_recipes = detect_missing_values(df_raw_recipes)
    missing_recipes_df = (
        missing_recipes[missing_recipes > 0]
        .sort_values(ascending=False)
        .to_frame(name="missing")
        .astype(int)
    )

    if missing_recipes_df.empty:
        st.success("✅ Aucune valeur manquante détectée dans *recipes*.")
    else:
        with st.expander("🔎 Nombre de valeurs manquantes", expanded=False):
            for col, val in missing_recipes_df["missing"].items():
                st.write(f"{col}: {val}")

    st.markdown(
        """**Imputations :**
- `description` manquante → `"No_description"`  
- ligne sans `name` → **supprimée** (indispensable)"""
    )

    st.markdown("### Valeurs extrêmes (minutes, n_ingredients, n_steps)")

    render_viz(
        "Boxplots minutes / n_ingredients / n_steps",
        plot_minutes_ningredients_nsteps,
        df_raw_recipes,
    )

    st.markdown(
        """On observe des **valeurs extrêmes** sur les trois colonnes, surtout `minutes`.
- Pour `minutes` on **retire** les recettes > **43200** (≈ 1 mois) — elles représentent ~0.03%.
"""
    )

    st.markdown("### Feature engineering : `nutrition` → colonnes dédiées")
    st.markdown(
        """On sépare `nutrition` en:
`calories`, `total_fat`, `sugar`, `sodium`, `protein`, `saturated_fat`, `carbohydrates`."""
    )

    # ⚠️ On travaille sur une copie locale pour l’aperçu
    _recipes_preview = df_raw_recipes.copy()
    _recipes_preview[
        [
            "calories",
            "total_fat",
            "sugar",
            "sodium",
            "protein",
            "saturated_fat",
            "carbohydrates",
        ]
    ] = _recipes_preview["nutrition"].str.split(",", expand=True)

    splitted_recipes = st.multiselect(
        "Colonnes à afficher (recipes)",
        _recipes_preview.columns.tolist(),
        default=_recipes_preview.columns.tolist()[:19],
    )
    st.dataframe(_recipes_preview[splitted_recipes].head(5), use_container_width=True)

    st.markdown(
        """**Seuils raisonnables** pour filtrer quelques extrêmes (exemples) :
- calories > **3000** → drop  
- carbohydrates / protein > **500 g** → drop  
- sodium > **5000 mg** → drop  
*(À adapter selon tes choix finaux dans le notebook de cleaning.)*"""
    )
