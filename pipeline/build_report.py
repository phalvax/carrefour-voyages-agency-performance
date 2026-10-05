
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

def add_hist(pdf, series, title, xlabel):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if len(s)==0: return
    fig = plt.figure(figsize=(11.69, 8.27))
    ax = fig.add_subplot(111)
    ax.hist(s, bins=20)
    ax.set_title(title); ax.set_xlabel(xlabel); ax.set_ylabel("Frequency")
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def add_table(pdf, title, df):
    fig = plt.figure(figsize=(11.69, 8.27)); plt.axis("off")
    plt.text(0.02, 0.95, title, fontsize=16, weight="bold")
    ax = fig.add_axes([0.02, 0.05, 0.96, 0.85]); ax.axis("off")
    tbl = ax.table(cellText=df.values, colLabels=df.columns, loc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(9); tbl.scale(1,1.3)
    pdf.savefig(fig, bbox_inches="tight"); plt.close(fig)

def main():
    base = Path(__file__).parents[1]
    cfg = yaml.safe_load(open(Path(__file__).with_name("config.yaml"), "r", encoding="utf-8"))
    out_dir = base / cfg["paths"]["outputs"]
    scores_path = out_dir / "agence_scores.csv"
    if not scores_path.exists():
        raise SystemExit("Run fusion_pipeline.py first to create outputs/agence_scores.csv")
    df = pd.read_csv(scores_path)

    tq = cfg["report"]["top_quantile"]; fq = cfg["report"]["flop_quantile"]; limit = cfg["report"]["tables_limit"]
    top_cut = df["score_global"].quantile(tq); flop_cut = df["score_global"].quantile(fq)
    top = df[df["score_global"]>=top_cut].sort_values("score_global", ascending=False).head(limit)
    flop = df[df["score_global"]<=flop_cut].sort_values("score_global", ascending=True).head(limit)

    pdf_path = out_dir / "rapport_agences.pdf"
    with PdfPages(pdf_path) as pdf:
        add_title(pdf, "Carrefour Voyages — Rapport Agences", "Top/Flop & distributions")
        add_text(pdf, "Méthode", ["Score global = combinaison pondérée des thèmes (config.yaml). "
                                  "Chaque thème = moyenne pondérée de z-scores, sens pris en compte via signe du poids."])
        add_text(pdf, "Distributions", ["Histogrammes des scores thématiques et du global."])
        for c in [x for x in df.columns if x.startswith("score_")]:
            add_hist(pdf, df[c], f"Distribution — {c}", c)
        show = [x for x in df.columns if x.startswith("score_")]
        add_table(pdf, "Top performers", top[["agency_key"]+show])
        add_table(pdf, "Flop performers", flop[["agency_key"]+show])
        add_text(pdf, "Lecture", ["Valeurs positives = au-dessus de la moyenne. "
                                  "Servez-vous des sous-scores pour décider des leviers locaux (staffing, digital, mix produits, etc.)."])
    print(f"PDF written: {pdf_path}")

if __name__ == "__main__":
    main()
