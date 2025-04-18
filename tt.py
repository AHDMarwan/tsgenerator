import streamlit as st
import json
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm

# ---- Configuration ----
ex1_total = 8
ex2_total = 8
ex3_total = 4  # Situation-problème total

def round_to_quarter(value):
    return round(value * 4) / 4

# ---- Load Courses ----
with open("courses2AC.json", "r", encoding="utf-8") as f:
    all_courses = json.load(f)
course_names = [course["name"] for course in all_courses]

# ---- Streamlit Setup & Navigation ----
st.set_page_config(page_title="Générateur de Spécification", layout="wide")
navigation = st.sidebar.radio("🔀 Navigation", ["🏠 Accueil", "📊 Générateur de Spécification"])

if navigation == "🏠 Accueil":
    st.title("Bienvenue ! 🎓")
    st.write("Créez facilement votre tableau de spécification. Utilisez le menu à gauche.")
else:
    # --- Sidebar Inputs ---
    st.sidebar.title("Informations sur l'examen")
    prof_name = st.sidebar.text_input("Nom de l'enseignant", "AIT HADDOU Marwan")
    school_name = st.sidebar.text_input("Nom de l'établissement", "Lycée Ibn Maja - Casablanca")
    semester = st.sidebar.number_input("Semestre", 1, 4, 2)
    current_year = datetime.now().year - 1
    years = [f"{y}-{y+1}" for y in range(current_year, current_year+10)]
    academic_year = st.sidebar.selectbox("Année scolaire", years)
    exam_number = st.sidebar.number_input("Numéro d'examen", 1, 10, 1)

    # --- Styles ---
    HEADER_BG = colors.HexColor("#2E86AB")
    HEADER_TEXT = colors.white
    STRIPE = colors.HexColor("#F5F5F5")
    GRID = colors.HexColor("#DDDDDD")
    cell_style = ParagraphStyle(name="Cell", fontSize=9, leading=12, wordWrap='CJK')
    def make_para(text): return Paragraph(text, cell_style)

    st.title("📄 Générateur de Spécification")
    selected = st.multiselect("Sélectionnez les cours :", course_names)

    if st.button("Générer la prévisualisation"):
        if not selected:
            st.warning("Veuillez sélectionner au moins un cours.")
        else:
            data = [c for c in all_courses if c['name'] in selected]
            total_h = sum(c['hours'] for c in data)
            pts_raw = [(c['hours']/total_h)*20 for c in data]
            pts_round = [round_to_quarter(p) for p in pts_raw]
            diff = sum(pts_round) - 20
            if diff != 0:
                idx = pts_round.index(max(pts_round)) if diff>0 else pts_round.index(min(pts_round))
                pts_round[idx] = round_to_quarter(pts_round[idx] - diff)

            # --- General Info ---
            gen = [
                [make_para("Nom de l'enseignant :"), make_para(prof_name), make_para("Établissement :"), make_para(school_name)],
                [make_para("Semestre :"), make_para(str(semester)), make_para("Année scolaire :"), make_para(academic_year)],
                [make_para("Numéro d'examen :"), make_para(str(exam_number)), make_para(""), make_para("")]
            ]

            # --- Details Table ---
            hdrs2 = ["Cours", "Objectifs d'apprentissage", "Capacités évaluables", "Connaissances évaluables"]
            det = [[make_para(h) for h in hdrs2]]
            for c in data:
                det.append([make_para(c['name']), make_para(c.get('objectives','')), make_para(c.get('Capacités évaluables','')), make_para(c.get('Connaissances évaluables',''))])

            # --- Calculations Table (omit per-course situation-problème) ---
            hdrs3 = ["Cours", "Heures", "%", "Barème (/20)", "Questions de cours", "Application", "Situation-problème"]
            calc = [[make_para(h) for h in hdrs3]]
            sum_q = sum_a = 0
            for i,c in enumerate(data):
                h = c['hours']; p = pts_round[i]
                perc = f"{(h/total_h)*100:.1f}%"
                q = round_to_quarter((p/20)*ex1_total)
                a = round_to_quarter((p/20)*ex2_total)
                sum_q += q; sum_a += a
                calc.append([make_para(c['name']), make_para(str(h)), make_para(perc), make_para(f"{p:.2f}"), make_para(f"{q:.2f}"), make_para(f"{a:.2f}"), make_para("")])
            # Total row: show only total situation-problème (ex3_total)
            calc.append([make_para("Total"), make_para(str(total_h)), make_para("100%"), make_para("20.00"), make_para(f"{sum_q:.2f}"), make_para(f"{sum_a:.2f}"), make_para(f"{ex3_total:.2f}")])

            # --- PDF Build ---
            path = "spec_table.pdf"
            doc = SimpleDocTemplate(path, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
            title = f"<b>Tableau de Spécification du Controle N°{exam_number} – Semestre {semester}, {academic_year}</b>"
            ts = ParagraphStyle(name="Title", fontSize=14, leading=18, alignment=1, fontName="Helvetica-Bold", textColor=HEADER_BG, spaceAfter=16)
            foot_style = ParagraphStyle(name="Footnote", fontSize=6, leading=8, alignment=0, textColor=colors.grey)
            footnote = Paragraph('Généré par "Générateur de tableau de spécification", AIT HADDOU Marwan', foot_style)

            # Base style
            base = [("BOX",(0,0),(-1,-1),1,GRID),("INNERGRID",(0,0),(-1,-1),0.5,GRID),("ALIGN",(0,0),(-1,-1),"CENTER"),("PAD",(0,0),(-1,-1),6)]

            t1 = Table(gen, colWidths=[40*mm,75*mm,40*mm,75*mm])
            t1.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),STRIPE)] + base))

            t2 = Table(det, colWidths=[50*mm,60*mm,60*mm,60*mm])
            t2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),HEADER_BG),("TEXTCOLOR",(0,0),(-1,0),HEADER_TEXT),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ROWBACKGROUNDS",(1,0),(-1,-1),[colors.white,STRIPE])] + base))

            t3 = Table(calc, colWidths=[50*mm,20*mm,20*mm,30*mm,40*mm,30*mm,40*mm])
            style3 = [("BACKGROUND",(0,0),(-1,0),HEADER_BG),("TEXTCOLOR",(0,0),(-1,0),HEADER_TEXT),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("ROWBACKGROUNDS",(1,0),(-1,-2),[colors.white,STRIPE]),("LINEABOVE",(0,-1),(-1,-1),1,HEADER_BG),("BACKGROUND",(0,-1),(-1,-1),HEADER_BG),("TEXTCOLOR",(0,-1),(-1,-1),HEADER_TEXT),("FONTNAME",(0,-1),(-1,-1),"Helvetica-Bold")] + base
            t3.setStyle(TableStyle(style3))

            # Build document with footnote
            doc.build([Paragraph(title, ts), Spacer(1, 12), t1, Spacer(1, 12), t2, Spacer(1, 12), t3, Spacer(1, 12), footnote])

            st.success(f"✅ PDF créé : {path}")
            with open(path, "rb") as f:
                st.download_button("📥 Télécharger", f, file_name=path, mime="application/pdf")
