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
ex3_total = 4

def round_to_quarter(value):
    return round(value * 4) / 4

# ---- Load Courses ----
with open("courses2AC.json", "r", encoding="utf-8") as f:
    all_courses = json.load(f)
course_names = [course["name"] for course in all_courses]

# ---- Streamlit Page Setup & Navigation ----
st.set_page_config(page_title="Générateur de tableau de spécification", layout="wide")
navigation = st.sidebar.radio("🔀 Navigation", ["🏠 Accueil", "📊 Générateur de spécification"])

if navigation == "🏠 Accueil":
    st.title("Bienvenue ! 🎓")
    st.markdown(
        "Cette application vous permet de créer un tableau de spécification pour vos examens."
    )
    st.markdown("**Instructions :**")
    st.write(
        "Utilisez le menu de navigation à gauche pour accéder au générateur de tableau."
    )
else:
    # ---- Sidebar Inputs ----
    st.sidebar.title("Informations de l’examen")
    prof_name = st.sidebar.text_input("Nom de l’enseignant", value="AIT HADDOU Marwan")
    school_name = st.sidebar.text_input("Établissement", value="Lycée Collègial Ibn Maja - Casablanca")
    semester = st.sidebar.number_input("Semestre", min_value=1, max_value=4, value=2)

    current_year = datetime.now().year - 1
    academic_years = [f"{y}-{y+1}" for y in range(current_year, current_year + 10)]
    academic_year = st.sidebar.selectbox("Année scolaire", academic_years, index=0)
    exam_number = st.sidebar.number_input("Numéro d'examen", min_value=1, value=1)

    # ---- Styling constants for modern look ----
    HEADER_BG = colors.HexColor("#4F81BD")
    HEADER_TEXT = colors.white
    STRIPE_BG = colors.HexColor("#F2F2F2")
    GRID_COLOR = colors.HexColor("#CCCCCC")
    cell_style = ParagraphStyle(name="Cell", fontSize=9, leading=11, wordWrap='CJK')
    def make_para(text):
        return Paragraph(text, cell_style)

    # ---- Main Page ----
    st.title("📄 Générateur de tableau de spécification")
    selected_courses = st.multiselect("Sélectionnez les cours :", course_names)

    if st.button("Prévisualiser le Tableau"):
        if not selected_courses:
            st.warning("Veuillez sélectionner au moins un cours.")
        else:
            selected_data = [c for c in all_courses if c["name"] in selected_courses]
            total_hours = sum(c["hours"] for c in selected_data)
            raw_points = [(c["hours"] / total_hours) * 20 for c in selected_data]
            rounded_points = [round_to_quarter(p) for p in raw_points]
            diff = sum(rounded_points) - 20
            if diff != 0:
                idx = rounded_points.index(max(rounded_points)) if diff > 0 else rounded_points.index(min(rounded_points))
                rounded_points[idx] = round_to_quarter(rounded_points[idx] - diff)

            # First Table: General Info
            general_info_data = [
                [make_para("Nom de l’enseignant :"), make_para(prof_name), make_para("Établissement :"), make_para(school_name)],
                [make_para("Semestre :"), make_para(str(semester)), make_para("Année scolaire :"), make_para(academic_year)],
                [make_para("Numéro de contrôle :"), make_para(str(exam_number)), make_para(""), make_para("")]
            ]

            # Second Table: Course Details
            headers = ["Nom du Cours", "Objectifs d'apprentissage", "Capacités évaluables", "Connaissances évaluables"]
            course_details_data = [[make_para(h) for h in headers]]
            for course in selected_data:
                course_details_data.append([
                    make_para(course["name"]), make_para(course.get("objectives", "")),
                    make_para(course.get("Capacités évaluables", "")), make_para(course.get("Connaissances évaluables", ""))
                ])

            # Third Table: Calculations + Totals
            calc_headers = ["Nom du Cours", "Volume horaire", "Pourcentage", "Barème (/20)",
                            "Questions de cours", "Application des connaissances", "Situation-problème"]
            course_calc_data = [[make_para(h) for h in calc_headers]]
            sum_qc = sum_app = sum_sp = 0
            for i, course in enumerate(selected_data):
                hours = course["hours"]
                pts = rounded_points[i]
                percent = f"{(hours/total_hours)*100:.2f}%"
                qc = round_to_quarter((pts/20)*ex1_total)
                app = round_to_quarter((pts/20)*ex2_total)
                sp = round_to_quarter((pts/20)*ex3_total)
                sum_qc += qc; sum_app += app; sum_sp += sp
                course_calc_data.append([
                    make_para(course["name"]), make_para(str(hours)), make_para(percent), make_para(f"{pts:.2f}"),
                    make_para(f"{qc:.2f} pts"), make_para(f"{app:.2f} pts"), make_para(f"{sp:.2f} pts")
                ])
            course_calc_data.append([
                make_para("Total"), make_para(str(total_hours)), make_para("100%"), make_para("20.00"),
                make_para(f"{sum_qc:.2f} pts"), make_para(f"{sum_app:.2f} pts"), make_para(f"{sum_sp:.2f} pts")
            ])

            # Build PDF
            file_path = "repartition_cours.pdf"
            doc = SimpleDocTemplate(file_path, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
            title_text = f"<b>Tableau de spécification N°{exam_number} – Semestre {semester}, Année scolaire {academic_year}</b>"
            title_style = ParagraphStyle(name="Title", fontSize=14, alignment=1, leading=16,
                                         spaceAfter=12, fontName="Helvetica-Bold", textColor=HEADER_BG)

            # Apply modern styles
            general_table = Table(general_info_data, colWidths=[40*mm,70*mm,40*mm,70*mm])
            general_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), STRIPE_BG),
                ("GRID", (0,0), (-1,-1), 0.25, GRID_COLOR),
                ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)
            ]))
            details_table = Table(course_details_data, colWidths=[50*mm,60*mm,60*mm,60*mm])
            details_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), HEADER_BG), ("TEXTCOLOR", (0,0), (-1,0), HEADER_TEXT),
                ("GRID", (0,0), (-1,-1), 0.25, GRID_COLOR),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, STRIPE_BG]),
                ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)
            ]))
            calc_table = Table(course_calc_data, colWidths=[50*mm,30*mm,30*mm,30*mm,60*mm,60*mm,60*mm])
            calc_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), HEADER_BG), ("TEXTCOLOR", (0,0), (-1,0), HEADER_TEXT),
                ("GRID", (0,0), (-1,-1), 0.25, GRID_COLOR),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, STRIPE_BG]),
                ("LEFTPADDING", (0,0), (-1,-1), 6), ("RIGHTPADDING", (0,0), (-1,-1), 6),
                ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)
            ]))

            # Generate PDF
            doc.build([Paragraph(title_text, title_style), Spacer(1,12), general_table, Spacer(1,12), details_table, Spacer(1,12), calc_table])
            st.success(f"✅ PDF généré avec succès : {file_path}")
            with open(file_path, "rb") as f:
                st.download_button(label="📥 Télécharger le PDF", data=f, file_name=file_path, mime="application/pdf")
