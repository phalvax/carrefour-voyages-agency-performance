
import pandas as pd, numpy as np, yaml, textwrap
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

def add_title(pdf, title, subtitle=None):
    fig = plt.figure(figsize=(11.69, 8.27)); plt.axis("off")
    plt.text(0.08, 0.8, title, fontsize=24, weight="bold")
    if subtitle: plt.text(0.08, 0.72, subtitle, fontsize=12)
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def add_text(pdf, heading, lines):
    fig = plt.figure(figsize=(11.69, 8.27)); plt.axis("off")
    y=0.9; plt.text(0.06, y, heading, fontsize=16, weight="bold"); y-=0.07
    for para in lines:
        wrapped = textwrap.fill(para, width=110)
        plt.text(0.06, y, wrapped, fontsize=11); y -= 0.06*(1+len(wrapped)//110)
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def add_table(pdf, title, df):
    fig = plt.figure(figsize=(11.69, 8.27)); plt.axis("off")
    plt.text(0.02, 0.95, title, fontsize=16, weight="bold")
    ax = fig.add_axes([0.02, 0.05, 0.96, 0.85]); ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1,1.2)
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def add_bars(pdf, xlabels, top_vals, flop_vals, title):
    import numpy as np
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_subplot(111)
    xi = np.arange(len(xlabels))
    w = 0.35
    ax.bar(xi - w/2, top_vals, width=w, label="Top 48")
    ax.bar(xi + w/2, flop_vals, width=w, label="Flop 48")
    ax.set_xticks(xi); ax.set_xticklabels(xlabels)
    ax.set_title(title); ax.legend()
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def describe_agency(row, score_cols):
    import numpy as np, pandas as pd
    parts = []
    for c in score_cols:
        val = row.get(c, np.nan)
        if pd.isna(val): continue
        if val >= 1.0:
            parts.append(f"{c} très fort (+)")
        elif val >= 0.3:
            parts.append(f"{c} au-dessus de la moyenne")
        elif val <= -1.0:
            parts.append(f"{c} très faible (-)")
        elif val <= -0.3:
            parts.append(f"{c} en dessous de la moyenne")
    return "; ".join(parts) if parts else "profil équilibré"

def main():
    base = Path(__file__).parents[1]
    cfg = yaml.safe_load(open(Path(__file__).with_name("config.yaml"), "r", encoding="utf-8"))
    out_dir = base / cfg["paths"]["outputs"]
    scores_path = out_dir / "agence_scores.csv"
    if not scores_path.exists():
        raise SystemExit("Run fusion_pipeline.py first to create outputs/agence_scores.csv")
    df = pd.read_csv(scores_path)

    if "CA_Total" not in df.columns:
        raise SystemExit("CA_Total missing from agence_scores.csv. Re-run fusion_pipeline.py (updated).")

    df_sorted = df.sort_values("CA_Total", ascending=False).reset_index(drop=True)

    n = len(df_sorted)
    k = min(48, n//2)
    top48 = df_sorted.head(k).copy()
    flop48 = df_sorted.tail(k).copy()

    score_cols = [c for c in df.columns if c.startswith("score_") and c!="score_global"]

    top_means = top48[score_cols].mean().to_dict()
    flop_means = flop48[score_cols].mean().to_dict()
    diff = {c: top_means.get(c, np.nan) - flop_means.get(c, np.nan) for c in score_cols}

    corr_rows = []
    if "score_performance" in df.columns:
        for c in score_cols:
            if c == "score_performance": continue
            corr = df[["score_performance", c]].corr().iloc[0,1]
            corr_rows.append({"with": c, "corr_vs_performance": corr})
    corr_df = pd.DataFrame(corr_rows).sort_values("corr_vs_performance", ascending=False) if corr_rows else pd.DataFrame()

    top5 = df_sorted.head(5).copy()
    flop5 = df_sorted.tail(5).copy()

    def mk_desc(r): return describe_agency(r, score_cols)
    top5["description"] = top5.apply(mk_desc, axis=1)
    flop5["description"] = flop5.apply(mk_desc, axis=1)

    # Exports
    top5_out = out_dir / "top5_by_CA.csv"
    flop5_out = out_dir / "flop5_by_CA.csv"
    summary_out = out_dir / "top48_flop48_scores_summary.csv"
    corr_out = out_dir / "correlations_vs_score_performance.csv"

    top5.to_csv(top5_out, index=False, encoding="utf-8")
    flop5.to_csv(flop5_out, index=False, encoding="utf-8")
    pd.DataFrame([top_means, flop_means, diff], index=["Top48_mean","Flop48_mean","Difference_TopMinusFlop"]).to_csv(summary_out, encoding="utf-8")
    if not corr_df.empty: corr_df.to_csv(corr_out, index=False, encoding="utf-8")

    pdf_path = out_dir / "rapport_top_flop_ca.pdf"
    with PdfPages(pdf_path) as pdf:
        add_title(pdf, "Analyse Top/Flop par Chiffre d'Affaires", "Top 48 vs Flop 48 + Top/Flop 5 détaillés")

        xlabels = [c.replace("score_","") for c in score_cols]
        top_vals = [top_means.get(c, np.nan) for c in score_cols]
        flop_vals = [flop_means.get(c, np.nan) for c in score_cols]
        add_bars(pdf, xlabels, top_vals, flop_vals, "Moyennes des scores (Top 48 vs Flop 48)")

        diff_df = pd.DataFrame({"score": score_cols, "diff_top_minus_flop": [diff[c] for c in score_cols]})
        add_table(pdf, "Écart (Top 48 - Flop 48) par score", diff_df.round(3))

        if not corr_df.empty:
            add_table(pdf, "Corrélation avec le score_performance (commerce)", corr_df.round(3))

        cols_to_show = ["agency_key", "CA_Total"] + score_cols + ["description"]
        add_table(pdf, "TOP 5 agences (triées par CA)", top5[cols_to_show].round(3))
        add_table(pdf, "FLOP 5 agences (triées par CA)", flop5[cols_to_show].round(3))

        add_text(pdf, "Notes & interprétation", [
            "Les scores sont des z-scores par thème. >0 = au-dessus de la moyenne réseau.",
            "L'écart Top-Flop révèle les leviers différenciants de la performance économique.",
            "Les corrélations vs score_performance orientent les priorités (clients, satisfaction, structure, concurrence)."
        ])
    print(f"PDF written: {pdf_path}")

if __name__ == "__main__":
    main()

df = pd.read_csv("outputs/agence_scores.csv")

q1, q2, q3 = df['score_global'].quantile([0.25, 0.50, 0.75])
def seg_global(x):
    if x >= q3: return "S1 - Excellence"
    if x >= q2: return "S2 - Solides"
    if x >= q1: return "S3 - Moyennes"
    return "S4 - Fragiles"

df["segment_global"] = df["score_global"].apply(seg_global)
print(df["segment_global"].value_counts())


df = pd.read_csv("outputs/agence_scores.csv")

# --- Segments déjà créés (si ce n'est pas déjà dans le DataFrame)
q1, q2, q3 = df['score_global'].quantile([0.25, 0.50, 0.75])
def seg_global(x):
    if x >= q3: return "S1 - Excellence"
    if x >= q2: return "S2 - Solides"
    if x >= q1: return "S3 - Moyennes"
    return "S4 - Fragiles"
df["segment_global"] = df["score_global"].apply(seg_global)

# --- Création du profil perf/sat
def quadrant_perf_sat(row):
    y = row['score_performance']
    x = row['score_satisfaction']
    if y >= 0 and x >= 0: return "Q1 Leaders"
    if y >= 0 and x < 0:  return "Q2 Commerciaux fragiles"
    if y < 0 and x >= 0:  return "Q3 Prometteurs"
    return "Q4 À redresser"

df["profil_perf_sat"] = df.apply(quadrant_perf_sat, axis=1)

# --- Statistiques par segment
tab_ps = df.groupby(["segment_global","profil_perf_sat"]).size().unstack(fill_value=0)
print(tab_ps)

tab_ps.to_csv("outputs/seg_profil_perf_sat.csv")
print("\n✅ Tableau enregistré : outputs/seg_profil_perf_sat.csv")


df["terrain_index"] = (df["score_structure"].fillna(0) + df["score_concurrence"].fillna(0)) / 2

def quadrant_clients_terrain(row):
    y = row['score_clients']
    x = row['terrain_index']
    if y >= 0 and x >= 0: return "CT1 Base solide / Terrain porteur"
    if y >= 0 and x < 0:  return "CT2 Base solide / Terrain difficile"
    if y < 0 and x >= 0:  return "CT3 Base faible / Terrain porteur"
    return "CT4 Base faible / Terrain difficile"

df["profil_clients_terrain"] = df.apply(quadrant_clients_terrain, axis=1)

tab_ct = df.groupby(["segment_global","profil_clients_terrain"]).size().unstack(fill_value=0)
print(tab_ct)

tab_ct.to_csv("outputs/seg_profil_clients_terrain.csv")
print("\n✅ Tableau enregistré : outputs/seg_profil_clients_terrain.csv")


plt.figure(figsize=(8,6))
plt.scatter(df["score_satisfaction"], df["score_performance"], c=df["score_global"], cmap="coolwarm")
plt.axhline(0, color='gray', linestyle='--')
plt.axvline(0, color='gray', linestyle='--')
plt.xlabel("Score Satisfaction")
plt.ylabel("Score Performance")
plt.title("Quadrant Performance vs Satisfaction")
plt.colorbar(label="Score global")
plt.show()


# ============================================
# analyse_performance_finale.py
# Analyse et segmentation finale des agences
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# === 1. Chargement du fichier source ===
df = pd.read_csv("outputs/agence_scores.csv")
print("✅ Données chargées :", df.shape, "lignes")

# === 2. Segmentation principale sur le score global ===
q1, q2, q3 = df['score_global'].quantile([0.25, 0.50, 0.75])
def segment_global(x):
    if x >= q3: return "S1 - Excellence"
    if x >= q2: return "S2 - Solides"
    if x >= q1: return "S3 - Moyennes"
    return "S4 - Fragiles"

df["segment_global"] = df["score_global"].apply(segment_global)
seg_counts = df["segment_global"].value_counts().sort_index()
print("\n=== Répartition des segments globaux ===")
print(seg_counts)

# === 3. Profil Performance ↔ Satisfaction ===
def quadrant_perf_sat(row):
    y = row.get('score_performance', 0)
    x = row.get('score_satisfaction', 0)
    if y >= 0 and x >= 0: return "Q1 Leaders"
    if y >= 0 and x < 0:  return "Q2 Commerciaux fragiles"
    if y < 0 and x >= 0:  return "Q3 Prometteurs"
    return "Q4 À redresser"

df["profil_perf_sat"] = df.apply(quadrant_perf_sat, axis=1)
tab_ps = df.groupby(["segment_global", "profil_perf_sat"]).size().unstack(fill_value=0)
tab_ps.to_csv("outputs/seg_profil_perf_sat.csv")
print("\n=== Profil Performance ↔ Satisfaction ===")
print(tab_ps)

# === 4. Profil Clients ↔ Terrain ===
df["terrain_index"] = (df["score_structure"].fillna(0) + df["score_concurrence"].fillna(0)) / 2
def quadrant_clients_terrain(row):
    y = row.get('score_clients', 0)
    x = row.get('terrain_index', 0)
    if y >= 0 and x >= 0: return "CT1 Base solide / Terrain porteur"
    if y >= 0 and x < 0:  return "CT2 Base solide / Terrain difficile"
    if y < 0 and x >= 0:  return "CT3 Base faible / Terrain porteur"
    return "CT4 Base faible / Terrain difficile"

df["profil_clients_terrain"] = df.apply(quadrant_clients_terrain, axis=1)
tab_ct = df.groupby(["segment_global", "profil_clients_terrain"]).size().unstack(fill_value=0)
tab_ct.to_csv("outputs/seg_profil_clients_terrain.csv")
print("\n=== Profil Clients ↔ Terrain ===")
print(tab_ct)

# === 5. Visualisation graphique ===
plt.figure(figsize=(8, 6))
plt.scatter(df["score_satisfaction"], df["score_performance"], c=df["score_global"], cmap="coolwarm", edgecolor="k", alpha=0.8)
plt.axhline(0, color='gray', linestyle='--')
plt.axvline(0, color='gray', linestyle='--')
plt.xlabel("Score Satisfaction")
plt.ylabel("Score Performance")
plt.title("Quadrant Performance vs Satisfaction")
plt.colorbar(label="Score global")
plt.tight_layout()
graph_path = "outputs/quadrant_perf_sat.png"
plt.savefig(graph_path)
plt.close()
print(f"\n📊 Graphique enregistré : {graph_path}")

# === 6. Corrélation avec le CA total ===
if "CA_Total" in df.columns:
    corr = df[["CA_Total","score_performance","score_clients","score_satisfaction","score_structure","score_concurrence","score_global"]].corr()["CA_Total"]
    corr_path = "outputs/correlation_CA.csv"
    corr.to_csv(corr_path)
    print(f"\n📈 Corrélations enregistrées : {corr_path}")
else:
    corr = None

# === 7. Génération d’un rapport PDF synthétique ===
pdf_path = "outputs/rapport_segmentation_agences.pdf"
doc = SimpleDocTemplate(pdf_path, pagesize=A4)
styles = getSampleStyleSheet()
story = []

story.append(Paragraph("<b>Analyse finale et segmentation des agences</b>", styles["Title"]))
story.append(Spacer(1, 12))

# Introduction
intro = """
Ce rapport présente la segmentation finale des agences à partir des scores calculés
dans le fichier <i>agence_scores.csv</i>. Les analyses reposent sur deux axes principaux :
(1) la performance et la satisfaction, et (2) la relation clients et le contexte terrain.
"""
story.append(Paragraph(intro, styles["Normal"]))
story.append(Spacer(1, 12))

# Segments globaux
story.append(Paragraph("<b>1. Répartition des segments globaux</b>", styles["Heading2"]))
data_seg = [["Segment", "Nombre d’agences"]] + [[idx, val] for idx, val in seg_counts.items()]
t = Table(data_seg)
t.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
story.append(t)
story.append(Spacer(1, 12))

# Performance / Satisfaction
story.append(Paragraph("<b>2. Profil Performance ↔ Satisfaction</b>", styles["Heading2"]))
data_ps = [ ["Segment"] + list(tab_ps.columns) ] + [ [idx] + list(row) for idx, row in tab_ps.iterrows() ]
t2 = Table(data_ps)
t2.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
story.append(t2)
story.append(Spacer(1, 12))

# Clients / Terrain
story.append(Paragraph("<b>3. Profil Clients ↔ Terrain</b>", styles["Heading2"]))
data_ct = [ ["Segment"] + list(tab_ct.columns) ] + [ [idx] + list(row) for idx, row in tab_ct.iterrows() ]
t3 = Table(data_ct)
t3.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
story.append(t3)
story.append(Spacer(1, 12))

# Corrélation
if corr is not None:
    story.append(Paragraph("<b>4. Corrélations avec le chiffre d’affaires</b>", styles["Heading2"]))
    data_corr = [["Variable", "Corrélation avec CA_Total"]] + [[i, round(v, 3)] for i, v in corr.items()]
    t4 = Table(data_corr)
    t4.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.lightgrey)]))
    story.append(t4)
    story.append(Spacer(1, 12))

story.append(Paragraph(f"<i>Graphique généré : {graph_path}</i>", styles["Normal"]))
story.append(Paragraph(f"<i>Données exportées : seg_profil_perf_sat.csv, seg_profil_clients_terrain.csv</i>", styles["Normal"]))

doc.build(story)
print(f"\n✅ Rapport PDF complet généré : {pdf_path}")
