import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from pathlib import Path

# === FICHIERS D'ENTRÉE ===
base = Path(__file__).parents[1]
data_path = base / "outputs" / "agences_segmentees_profils.csv"
graph_path = base / "outputs" / "repartition_segments_agences.png"
output_path = base / "outputs" / "Rapport_Segmentation_Agences.pdf"

# === CHARGEMENT DES DONNÉES ===
df = pd.read_csv(data_path, sep=";")

# === CONFIGURATION DU DOCUMENT ===
# ⚠️ Conversion du Path en chaîne ici ↓
doc = SimpleDocTemplate(str(output_path), pagesize=A4)
styles = getSampleStyleSheet()
story = []

# --- TITRE ---
story.append(Paragraph("<b>Rapport de Segmentation des Agences</b>", styles["Title"]))
story.append(Spacer(1, 20))

# --- INTRODUCTION ---
intro = """
Ce rapport présente la segmentation manuelle des agences réalisée à partir du score global obtenu
sur plusieurs dimensions clés : performance, satisfaction, clientèle, structure et concurrence.
Cette segmentation vise à identifier les forces et faiblesses du réseau pour guider les actions stratégiques.
"""
story.append(Paragraph(intro, styles["BodyText"]))
story.append(Spacer(1, 20))

# --- GRAPHIQUE ---
story.append(Paragraph("<b>Répartition des agences par segment</b>", styles["Heading2"]))
story.append(Spacer(1, 10))
story.append(Image(str(graph_path), width=400, height=250))  # ⚠️ str() ici aussi
story.append(Spacer(1, 20))

# --- DESCRIPTION DES SEGMENTS ---
desc = """
Les agences ont été réparties en quatre segments selon leur score global :
<ul>
<li><b>S1 - Excellence</b> : agences performantes et équilibrées, références du réseau.</li>
<li><b>S2 - Solides</b> : agences stables avec un bon potentiel de croissance.</li>
<li><b>S3 - Moyennes</b> : agences présentant des performances intermédiaires.</li>
<li><b>S4 - Fragiles</b> : agences en difficulté nécessitant un accompagnement prioritaire.</li>
</ul>
"""
story.append(Paragraph(desc, styles["BodyText"]))
story.append(Spacer(1, 20))

# --- TABLEAU DES SEGMENTS ---
counts = df["segment_global"].value_counts().sort_index()
data = [["Segment", "Nombre d'agences"]] + [[seg, int(nb)] for seg, nb in counts.items()]
table = Table(data, colWidths=[200, 150])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ALIGN", (1, 1), (-1, -1), "CENTER")
]))
story.append(table)
story.append(Spacer(1, 20))

# --- EXEMPLES DE PROFILS ---
story.append(Paragraph("<b>Exemples de profils d’agences</b>", styles["Heading2"]))
story.append(Spacer(1, 10))
sample = df[["agency_key", "segment_global", "profil_general"]].head(10)
sample_data = [["ID Agence", "Segment", "Profil"]] + sample.values.tolist()
sample_table = Table(sample_data, colWidths=[100, 150, 250])
sample_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
]))
story.append(sample_table)
story.append(Spacer(1, 20))

# --- CONCLUSION ---
conclusion = """
Cette segmentation met en évidence la structure globale du réseau d’agences.
Les segments S1 et S2 représentent la force du groupe, tandis que S3 et S4
définissent les zones d'amélioration prioritaires. Une analyse complémentaire
du chiffre d'affaires et de la satisfaction permettra d'affiner les priorités
et d'orienter les plans d’action commerciaux.
"""
story.append(Paragraph(conclusion, styles["BodyText"]))

# --- GÉNÉRATION DU PDF ---
doc.build(story)

print(f"✅ Rapport PDF généré : {output_path}")
