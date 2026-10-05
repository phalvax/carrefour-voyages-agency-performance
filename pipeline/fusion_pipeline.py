import pandas as pd, numpy as np, yaml
from pathlib import Path

def load_xlsx(path):
    try:
        return pd.read_excel(path)
    except Exception as e:
        print(f"Warning reading {path}: {e}")
        return pd.DataFrame()

def pick_col(df, candidates):
    """Cherche la première colonne existante parmi la liste 'candidates'."""
    if df is None or df.empty:
        return None
    if not candidates:
        return None
    cols_lower = {c.lower().strip(): c for c in df.columns}
    for cand in candidates:
        if cand is None:
            continue
        key = cand.lower().strip()
        if key in cols_lower:
            return cols_lower[key]
    return None

def c(df, key, cols=None):
    """Retourne la colonne correspondant à la clé 'key' depuis la config YAML."""
    if cols is None:
        return None
    if key not in cols:
        print(f"⚠️ Clé '{key}' absente du fichier config.yaml")
        return None
    candidates = cols[key]
    col = pick_col(df, candidates)
    if not col:
        print(f"⚠️ Aucune colonne trouvée dans {df.shape[1]} colonnes pour la clé '{key}' ({candidates})")
    return col


def main():
    cfg = yaml.safe_load(open(Path(__file__).with_name("config.yaml"), "r", encoding="utf-8"))
    base = Path(__file__).parents[1]
    data_dir = base / cfg["paths"]["data_raw"]
    out_dir = base / cfg["paths"]["outputs"]
    out_dir.mkdir(parents=True, exist_ok=True)

    cols = cfg["columns"]; themes = cfg["themes"]; weights_theme = cfg["theme_weights"]
    files = cfg["files"]

    perf = load_xlsx(data_dir / files["Global_Perf_Agences_Mensuel"])
    clients = load_xlsx(data_dir / files["Synthese_BDD_Clients_Agences"])
    satisf = load_xlsx(data_dir / files["Satisfaction_Clients_Agences_Trimestres"])
    recrut = load_xlsx(data_dir / files["Recrutement_Agences_Mensuel"])
    attrs = load_xlsx(data_dir / files["Attributs_Agences_Magasins"])
    concurr = load_xlsx(data_dir / files["Attributs_Magasins_Concurrents_LECLERC"])
    trans = load_xlsx(data_dir / files["Transactions_Magasins_Mensuelles"])


    # Aggregate performance by agency
    perf_ca_col = None
    if not perf.empty:
        ag = c(perf, "agency_id", cols) or c(perf, "agency_name", cols)
    
        # Détection des colonnes à agréger
        ca_col = c(perf, "perf_CA_total", cols)
        nbresa_col = c(perf, "perf_nb_resa", cols)
        caweb_col = c(perf, "perf_CA_web", cols)

        # 👉 Diagnostics (après initialisation)
        # print("Colonnes dans perf :", perf.columns.tolist())
        # print("Colonne agency_id trouvée :", c(perf, "agency_id", cols))
        # print("Colonne agency_name trouvée :", c(perf, "agency_name", cols))
        # print("✅ Colonnes trouvées pour performance:")
        # print("CA total:", ca_col)
        # print("Nombre de résa:", nbresa_col)
        # print("CA web:", caweb_col)

        # Construction du dictionnaire d'agrégation
        agg_dict = {}
        if ca_col: 
            agg_dict[ca_col] = "sum"
            perf_ca_col = ca_col
        if nbresa_col:
            agg_dict[nbresa_col] = "sum"
        if caweb_col:
            agg_dict[caweb_col] = "sum"

        print("Agg dict:", agg_dict)

        # Agrégation
        gperf = perf.groupby(ag).agg(agg_dict).reset_index().rename(columns={ag: "agency_key"})
    else:
        gperf = pd.DataFrame(columns=["agency_key"])

        # Clients
    if not clients.empty:
        ag2 = c(clients, "agency_id", cols) or c(clients, "agency_name", cols)
        gcli = clients.groupby(ag2).agg({
            c(clients, "cli_nb_actifs", cols): "sum" if c(clients, "cli_nb_actifs", cols) else "mean",
            c(clients, "cli_nb_fideles", cols): "sum" if c(clients, "cli_nb_fideles", cols) else "mean",
            c(clients, "cli_valeur_annuelle", cols): "mean" if c(clients, "cli_valeur_annuelle", cols) else "mean",
        }).reset_index().rename(columns={ag2: "agency_key"})
    else:
        gcli = pd.DataFrame(columns=["agency_key"])


    # Recrutement
        # Recrutement
    if not recrut.empty:
        ag3 = c(recrut, "agency_id", cols) or c(recrut, "agency_name", cols)
        
        # print("\n=== DIAGNOSTIC RECRUTEMENT ===")
        # print("Colonnes du fichier Recrutement :", recrut.columns.tolist())
        # print("Colonne agency_id trouvée :", c(recrut, "agency_id", cols))
        # print("Colonne agency_name trouvée :", c(recrut, "agency_name", cols))
        # print("Colonne recrut_evolution_nouveaux :", c(recrut, "recrut_evolution_nouveaux", cols))
        # print("Colonne recrut_poids_CA_nouveaux :", c(recrut, "recrut_poids_CA_nouveaux", cols))
        
        grec = recrut.groupby(ag3).agg({
            c(recrut, "recrut_evolution_nouveaux", cols): "mean" if c(recrut, "recrut_evolution_nouveaux", cols) else "mean",
            c(recrut, "recrut_poids_CA_nouveaux", cols): "mean" if c(recrut, "recrut_poids_CA_nouveaux", cols) else "mean",
        }).reset_index().rename(columns={ag3: "agency_key"})
    else:
        grec = pd.DataFrame(columns=["agency_key"])


    # Satisfaction
        # Satisfaction
    if not satisf.empty:
        ag4 = c(satisf, "agency_id", cols) or pick_col(satisf, ["Agence_Code_CIE"])
        
        # print("\n=== DIAGNOSTIC SATISFACTION ===")
        # print("Colonnes du fichier Satisfaction :", satisf.columns.tolist())
        # print("Colonne agency_id trouvée :", c(satisf, "agency_id", cols))
        # print("Colonne agency_name trouvée :", c(satisf, "agency_name", cols))
        # print("Colonne satisfaction_nps :", c(satisf, "satisfaction_nps", cols))
        # print("Colonne satisfaction_respondents :", c(satisf, "satisfaction_respondents", cols))

        gsat = satisf.groupby(ag4).agg({
            c(satisf, "satisfaction_nps", cols): "mean" if c(satisf, "satisfaction_nps", cols) else "mean",
            c(satisf, "satisfaction_respondents", cols): "sum" if c(satisf, "satisfaction_respondents", cols) else "sum",
        }).reset_index().rename(columns={ag4:"agency_key"})
    else:
        gsat = pd.DataFrame(columns=["agency_key"])


    # Attributs (store link)
        # Attributs (store link)
    if not attrs.empty:
        ag5 = c(attrs, "agency_id", cols) or c(attrs, "agency_name", cols)

        # print("\n=== DIAGNOSTIC ATTRIBUTS ===")
        # print("Colonnes du fichier Attributs :", attrs.columns.tolist())
        # print("Colonne agency_id trouvée :", c(attrs, "agency_id", cols))
        # print("Colonne agency_name trouvée :", c(attrs, "agency_name", cols))
        # print("Colonne struct_surface :", c(attrs, "struct_surface", cols))
        # print("Colonne struct_format :", c(attrs, "struct_format", cols))
        # print("Colonne struct_statut :", c(attrs, "struct_statut", cols))
        # print("Colonne struct_drive :", c(attrs, "struct_drive", cols))
        # print("Colonne store_id :", c(attrs, "store_id", cols))

        gatt = attrs.groupby(ag5).agg({
            c(attrs, "struct_surface", cols): "mean" if c(attrs, "struct_surface", cols) else "mean",
            c(attrs, "struct_format", cols): "first" if c(attrs, "struct_format", cols) else "first",
            c(attrs, "struct_statut", cols): "first" if c(attrs, "struct_statut", cols) else "first",
            c(attrs, "struct_drive", cols): "max" if c(attrs, "struct_drive", cols) else "max",
            c(attrs, "store_id", cols): "first" if c(attrs, "store_id", cols) else "first"
        }).reset_index().rename(columns={ag5: "agency_key"})
    else:
        gatt = pd.DataFrame(columns=["agency_key"])


    # Merge thematic agency-level
    df = gperf
    for part in (gcli, grec, gsat, gatt):
        if df.empty:
            df = part.copy()
        else:
            df = df.merge(part, on="agency_key", how="outer")

    # Bring competition via store link
    if not df.empty:
        # try to detect store column
        store_col = None
        for ccol in df.columns:
            if "Magasin_Code" in ccol or ccol.lower().endswith("store_id") or "store_key" in ccol:
                store_col = ccol
        if store_col:
            df = df.rename(columns={store_col:"store_key"})

    # Competition datasets aggregated by store
    if not trans.empty:
        # print("\n=== DIAGNOSTIC TRANSACTIONS ===")
        # print("Colonnes du fichier Transactions :", trans.columns.tolist())
        st = c(trans, "store_id", cols)
        # print("Colonne store_id trouvée :", st)
        tx = c(trans, "tx_panier_moyen", cols)
        # print("Colonne tx_panier_moyen trouvée :", tx)

        if st is None:
            # print("❌ Aucune colonne de type store_id trouvée dans le fichier Transactions. Vérifie config.yaml.")
            pass
        else:
            gtrans = trans.groupby(st).agg({
                tx: "mean" if tx else "mean"
            }).reset_index().rename(columns={st:"store_key"})
    else:
        gtrans = pd.DataFrame(columns=["store_key"])


    if not concurr.empty:
        print("\n=== DIAGNOSTIC CONCURRENCE ===")
        print("Colonnes du fichier Concurrence :", concurr.columns.tolist())

        st2 = c(concurr, "store_id", cols)
        print("Colonne store_id trouvée :", st2)
        dist = c(concurr, "conc_distance_compet", cols)
        print("Colonne conc_distance_compet trouvée :", dist)

        if st2 is None:
            print("❌ Aucune colonne 'store_id' trouvée dans le fichier Concurrence. Vérifie config.yaml.")
        else:
            gconc = concurr.groupby(st2).agg({
                dist: "mean" if dist else "mean"
            }).reset_index().rename(columns={st2:"store_key"})
    else:
        gconc = pd.DataFrame(columns=["store_key"])


    if "store_key" in df.columns:
        if not gtrans.empty:
            df = df.merge(gtrans, on="store_key", how="left")
        if not gconc.empty:
            df = df.merge(gconc, on="store_key", how="left")

    # Build theme scores
    def resolve_vars(keys):
        found = []
        for k in keys:
            cands = cols[k]
            f = None
            for cand in cands:
                for existing in df.columns:
                    if existing.lower().strip() == cand.lower().strip():
                        f = existing; break
                if f: break
            if f: found.append(f)
        return found

    for theme, meta in themes.items():
        keys = meta["vars"]; w = meta["weights"]
        use_cols = resolve_vars(keys)
        if not use_cols:
            df[f"score_{theme}"] = np.nan
            continue
        # align weights to found cols
        aligned_w = []
        for k in keys:
            if any(existing.lower().strip() in [c.lower().strip() for c in cols[k]] for existing in use_cols):
                aligned_w.append(meta["weights"][keys.index(k)])
        mats = []; absw = []
        for i, ccol in enumerate(use_cols):
            w_i = aligned_w[i] if i < len(aligned_w) else 1.0
            s = pd.to_numeric(df[ccol], errors="coerce")
            std = s.std(ddof=0)
            z = (s - s.mean()) / std if std not in (0, np.nan, None) and not pd.isna(std) else pd.Series(np.zeros(len(s)))
            mats.append(z * np.sign(w_i))
            absw.append(abs(w_i))
        M = np.vstack([m.fillna(0).values for m in mats]).T
        absw = np.array(absw, dtype=float); absw = absw / (absw.sum() if absw.sum()!=0 else 1.0)
        df[f"score_{theme}"] = (M @ absw)

    # Global score
    sg = 0.0; tw = 0.0
    for t, w in weights_theme.items():
        coln = f"score_{t}"
        if coln in df.columns:
            sg += w * df[coln].fillna(0)
            tw += w
    df["score_global"] = sg / (tw if tw>0 else 1.0)

    # Prepare output columns
    keep = ["agency_key"]
    if "store_key" in df.columns: keep.append("store_key")
    score_cols = [c for c in df.columns if c.startswith("score_")]
    keep += score_cols

    # Also keep raw CA total for sorting in later analysis
    if perf_ca_col and perf_ca_col in df.columns:
        df = df.rename(columns={perf_ca_col: "CA_Total"})
        keep.append("CA_Total")

    out = df[keep].sort_values("score_global", ascending=False)
    out_path = out_dir / "agence_scores.csv"
    out.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Exported: {out_path}")

if __name__ == "__main__":
    main()
