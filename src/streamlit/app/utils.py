import pandas as pd
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
    Retourne un dict avec des DataFrames ou None en cas d'erreur.
    """
    ds = {}

    def _safe(name, fn):
        try:
            return fn()
        except Exception as e:
            print(f"[utils.get_ds] WARN: '{name}' not loaded: {e}")
            return None

    ds["raw_recipes"]        = _safe("raw_recipes", load_recipes_data)
    ds["raw_interactions"]   = _safe("raw_interactions", load_interactions_data)
    ds["clean_recipes"]      = _safe("clean_recipes", load_clean_recipes)
    ds["clean_interactions"] = _safe("clean_interactions", load_clean_interactions)
    ds["merged"]             = _safe("merged", load_clean_merged)

    return ds
