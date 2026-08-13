from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


OUT = Path("output/pdf/Ahmad_CV_MHA_DataAnalyst_Template.pdf")


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace(" &amp;nbsp;", " ")


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "CVName",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#2f3744"),
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        "CVRole",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=12,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
    )
)
styles.add(
    ParagraphStyle(
        "CVContact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.8,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#3f3f3f"),
        spaceAfter=12,
    )
)
styles.add(
    ParagraphStyle(
        "CVSection",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=14,
        textColor=colors.black,
        spaceBefore=8,
        spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        "CVBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#222222"),
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        "CVTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#222222"),
        spaceBefore=5,
        spaceAfter=1,
    )
)
styles.add(
    ParagraphStyle(
        "CVTech",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9.2,
        leading=12,
        textColor=colors.HexColor("#555555"),
        spaceAfter=3,
    )
)
styles.add(
    ParagraphStyle(
        "CVBullet",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.6,
        leading=13.4,
        leftIndent=14,
        firstLineIndent=-7,
        bulletIndent=1,
        textColor=colors.HexColor("#222222"),
        spaceAfter=3.7,
    )
)
styles.add(
    ParagraphStyle(
        "CVRight",
        parent=styles["CVBody"],
        alignment=TA_RIGHT,
        fontName="Helvetica-Oblique",
    )
)


def p(text: str, style: str = "CVBody") -> Paragraph:
    return Paragraph(esc(text), styles[style])


def section(story, title: str):
    story.append(p(title.upper(), "CVSection"))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.black, spaceBefore=0, spaceAfter=7))


def bullets(items):
    return ListFlowable(
        [ListItem(p(item, "CVBullet"), bulletColor=colors.black) for item in items],
        bulletType="bullet",
        start="circle",
        leftIndent=0,
        bulletFontSize=5,
        spaceAfter=2,
    )


def project(story, title, tech, items):
    story.append(p(title, "CVTitle"))
    story.append(p(tech, "CVTech"))
    story.append(bullets(items))


def page_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.white)
    canvas.drawString(0.5 * cm, 0.5 * cm, "")
    canvas.restoreState()


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.65 * cm,
        rightMargin=1.65 * cm,
        topMargin=1.55 * cm,
        bottomMargin=1.5 * cm,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal", showBoundary=0)
    doc.addPageTemplates([PageTemplate(id="cv", frames=[frame], onPage=page_footer)])

    story = []
    story.append(p("SYED MUHAMMAD AHMAD BOKHARI", "CVName"))
    story.append(p("Data Analyst | SQL, Power BI & Insight-Led Storytelling", "CVRole"))
    story.append(
        p(
            "07769685019 | bokhariahmed765@gmail.com | linkedin.com/in/syed-muhammad-ahmad-bokhari-aa5064294<br/>github.com/syedahmadbokhari",
            "CVContact",
        )
    )

    section(story, "Personal Summary")
    story.append(
        p(
            "AI & Data Professional with a First-Class degree from the University of Bradford. I use SQL, Power BI, Excel, Python and dbt to turn raw data into clear insight, dashboards and practical recommendations. Project experience includes data transformation, KPI reporting, service-focused analysis, validation checks and insight-led storytelling for technical and non-technical stakeholders, with a strong interest in using data to improve services and community outcomes."
        )
    )

    section(story, "Education")
    edu = Table(
        [[Paragraph("<b>BSc (Hons) Applied Artificial Intelligence - University of Bradford</b>", styles["CVBody"]), Paragraph("<i>2023 - 2026</i>", styles["CVRight"])]],
        colWidths=[doc.width * 0.72, doc.width * 0.28],
    )
    edu.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(edu)
    story.append(p("First Class Honours"))

    section(story, "Projects")
    project(
        story,
        "UK Crime Data Pipeline - Public Service Insight & Reporting",
        "Python, SQL, DuckDB, dbt, Airflow, FastAPI, Great Expectations, Streamlit",
        [
            "<b>Built public-service dashboards</b> for crime trends, category breakdowns, geographic hotspots and force KPIs, turning complex operational data into insight stakeholders could act on.",
            "<b>Created an end-to-end data workflow</b> from source CSV ingestion through DuckDB warehouse tables, dbt staging/marts, Airflow orchestration and Streamlit reporting.",
            "<b>Automated data quality checks</b> for schema, nulls, accepted values, row counts, coordinate ranges and unique IDs so reporting outputs stayed accurate and trustworthy.",
            "<b>Used insight-led storytelling</b> to explain trends, risks, outcome rates and hotspot patterns in plain language for non-technical users.",
        ],
    )
    project(
        story,
        "Retail Data Platform - Power BI, Excel & Commercial Insight",
        "SQL, Python, PostgreSQL, dbt, Airflow, Power BI, Tableau, Excel, Snowflake, Docker",
        [
            "<b>Designed Power BI, Tableau and Excel reports</b> covering revenue, discount impact, traffic trends, product performance and pricing opportunities for decision-making.",
            "<b>Modelled clean reporting datasets</b> across raw, clean and analytics layers using SQL and dbt, creating repeatable KPI tables for dashboard use.",
            "<b>Used SQL analysis</b> with CTEs, window functions, joins and aggregations to identify performance trends, risks and opportunities.",
            "<b>Improved reporting confidence</b> by identifying 354 corrupted GBP 0 price records before feature engineering and downstream dashboard use.",
        ],
    )
    project(
        story,
        "AI for Environmental Monitoring & Urban Planning - BSc final-year project",
        "Python, OpenCV, PyTorch (MobileNetV3), MOG2, ByteTrack, YOLOv8, Flask, GIS",
        [
            "<b>Translated AI outputs into a service workflow</b> with alerts, snapshots, confidence scores and GIS hotspot mapping for practical stakeholder review.",
            "<b>Evaluated the system against manually observed ground truth</b>, reporting 75% accuracy and 60% recall while explaining model tradeoffs clearly.",
            "<b>Designed a feedback-led improvement process</b> where dismissed alerts become retraining data, supporting continuous improvement and better future performance.",
        ],
    )

    story.append(PageBreak())
    section(story, "Work Experience")
    exp = Table(
        [[Paragraph("<b>AI Project Lead, Bradford Council</b>", styles["CVBody"]), Paragraph("<i>Jul 2026 - Present</i>", styles["CVRight"])]],
        colWidths=[doc.width * 0.72, doc.width * 0.28],
    )
    exp.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(exp)
    story.append(
        bullets(
            [
                "<b>Leading a data-driven AI monitoring project</b> for a local council, translating a detection system into reporting stakeholders can act on",
                "Coordinating requirements and reporting cadence with Council stakeholders within governance and data protection constraints",
                "Leading a team of three across a ~6-month engagement, with fortnightly reporting to Council and academic stakeholders",
            ]
        )
    )

    section(story, "Technical Skills")
    for line in [
        "<b>SQL & Data Analysis:</b> SQL, CTEs, window functions, multi-table joins, trend analysis, performance insight, risk/opportunity identification",
        "<b>Power BI & Reporting:</b> Power BI, DAX concepts, Excel, Tableau, Streamlit, KPI dashboards, self-serve reporting, insight-led storytelling",
        "<b>Data Transformation:</b> Python, Pandas, NumPy, dbt, PostgreSQL, DuckDB, ETL pipelines, clean analytics layers, data workflow mapping",
        "<b>Data Quality:</b> validation gates, schema testing, accepted-value checks, null handling, reconciliation, automated checks, auditable assumptions",
        "<b>Digital & Service Improvement:</b> dashboard adoption, process improvement, customer-focused insight, community/public-sector data, continuous improvement",
        "<b>Collaboration:</b> requirements gathering, stakeholder reporting, technical/non-technical communication, Git/GitHub, documentation, team working",
    ]:
        story.append(p(line))

    section(story, "Certifications")
    story.append(bullets(["Data Fundamentals & AI Fundamentals Certificates, IBM SkillsBuild (2026)"]))

    section(story, "Soft Skills")
    story.append(p("Problem-Solving, Teamwork, Communication, Stakeholder Reporting."))

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
