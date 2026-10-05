import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# === CONFIGURATION ===
file_name = "agence_scores - agence_scores.csv.csv"

base = Path(__file__).parents[1]
data_dir = base / "data_raw"
out_dir = base / "outputs"
out_dir.mkdir(parents=True, exist_ok=True)

# === CHARGEMENT DU FICHIER ===
file_path = data_dir / file_name
df = pd.read_csv(file_path, sep=",", encoding="utf-8")  # <== ici : virgule
print("Colonnes détectées :", df.columns.tolist())

# Sélection des lignes utiles
subset = pd.concat([df.iloc[3:98], df.iloc[[99, 106]]], ignore_index=True)

# === SEGMENTATION EN QUARTILES ===
quartiles = subset["score_globale"].quantile([0.25, 0.5, 0.75])
q1, q2, q3 = quartiles[0.25], quartiles[0.5], quartiles[0.75]

def assign_segment(score):
    if score >= q3:
        return "S1 - Excellence"
    elif score >= q2:
        return "S2 - Solides"
    elif score >= q1:
        return "S3 - Moyennes"
    else:
        return "S4 - Fragiles"

subset["segment_global"] = subset["score_globale"].apply(assign_segment)

# === PROFIL DESCRIPTIF PAR SEGMENT ===
def profil_description(segment):
    return {
        "S1 - Excellence": "Agence performante et équilibrée",
        "S2 - Solides": "Agence stable avec bon potentiel",
        "S3 - Moyennes": "Agence moyenne avec axes d'amélioration",
        "S4 - Fragiles": "Agence en difficulté commerciale"
    }[segment]

subset["profil_general"] = subset["segment_global"].apply(profil_description)

# === SAUVEGARDE DU FICHIER SEGMENTÉ ===
output_csv = out_dir / "agences_segmentees_profils.csv"
subset.to_csv(output_csv, index=False, sep=";", encoding="utf-8")
print(f"✅ Fichier segmenté enregistré : {output_csv}")

# === VISUALISATION ===
plt.figure(figsize=(8, 5))
subset["segment_global"].value_counts().sort_index().plot(
    kind="bar",
    color=["#2ecc71", "#3498db", "#f1c40f", "#e74c3c"]
)
plt.title("Répartition des agences par segment de performance", fontsize=13)
plt.xlabel("Segment")
plt.ylabel("Nombre d'agences")
plt.xticks(rotation=0)
plt.tight_layout()

output_graph = out_dir / "repartition_segments_agences.png"
plt.savefig(output_graph, dpi=300)
plt.close()
print(f"✅ Graphique enregistré : {output_graph}")

# === SYNTHÈSE ===
print("\n=== Résumé des segments ===")
print(subset["segment_global"].value_counts().sort_index())
print("\nExemples de profils :")
print(subset[["agency_key", "segment_global", "profil_general"]].head(10))
