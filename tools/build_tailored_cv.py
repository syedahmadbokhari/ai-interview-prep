from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_RIGHT
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
)


OUT = Path("output/pdf/Ahmad_Bokhari_CV_Graduate_Business_Analyst_AstonMartinF1.pdf")


def clean(text: str) -> str:
    return text.replace("&", "&amp;")


styles = getSampleStyleSheet()
styles.add(
    ParagraphStyle(
        "Name",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=21,
        textColor=colors.HexColor("#1f2933"),
        spaceAfter=2,
    )
)
styles.add(
    ParagraphStyle(
        "Role",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.8,
        leading=13,
        textColor=colors.HexColor("#3f4f5f"),
        spaceAfter=7,
    )
)
styles.add(
    ParagraphStyle(
        "Contact",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.3,
        leading=10.5,
        textColor=colors.HexColor("#303b45"),
        alignment=TA_RIGHT,
    )
)
styles.add(
    ParagraphStyle(
        "Section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9.4,
        leading=11,
        textColor=colors.HexColor("#0f3d5e"),
        spaceBefore=8,
        spaceAfter=4,
    )
)
styles.add(
    ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.6,
        leading=10.8,
        textColor=colors.HexColor("#202932"),
        spaceAfter=3,
    )
)
styles.add(
    ParagraphStyle(
        "Tight",
        parent=styles["Body"],
        spaceAfter=1.8,
    )
)
styles.add(
    ParagraphStyle(
        "Subhead",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.9,
        leading=10.7,
        textColor=colors.HexColor("#111827"),
        spaceBefore=3,
        spaceAfter=1.4,
    )
)
styles.add(
    ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.1,
        leading=9.8,
        textColor=colors.HexColor("#52616f"),
        spaceAfter=1.6,
    )
)
styles.add(
    ParagraphStyle(
        "CVBullet",
        parent=styles["Body"],
        leftIndent=12,
        firstLineIndent=-6,
        bulletIndent=2,
        spaceAfter=1.4,
    )
)


def para(text, style="Body"):
    return Paragraph(clean(text), styles[style])


def bullet_list(items):
    return ListFlowable(
        [
            ListItem(
                Paragraph(clean(item), styles["CVBullet"]),
                bulletColor=colors.HexColor("#0f3d5e"),
            )
            for item in items
        ],
        bulletType="bullet",
        start="circle",
        leftIndent=0,
        bulletFontSize=4.8,
        spaceAfter=2,
    )


def header(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#d8e1e8"))
    canvas.setLineWidth(0.7)
    canvas.line(1.55 * cm, 1.18 * cm, A4[0] - 1.55 * cm, 1.18 * cm)
    canvas.setFont("Helvetica", 7.4)
    canvas.setFillColor(colors.HexColor("#687584"))
    canvas.drawRightString(A4[0] - 1.55 * cm, 0.72 * cm, f"Page {doc.page}")
    canvas.restoreState()


def add_section(story, title):
    story.append(para(title.upper(), "Section"))
    story.append(
        HRFlowable(
            width="100%",
            thickness=0.7,
            color=colors.HexColor("#d8e1e8"),
            spaceBefore=0,
            spaceAfter=3,
        )
    )


def add_project(story, title, meta, bullets):
    story.append(para(title, "Subhead"))
    story.append(para(meta, "Meta"))
    story.append(bullet_list(bullets))


def build():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = BaseDocTemplate(
        str(OUT),
        pagesize=A4,
        leftMargin=1.55 * cm,
        rightMargin=1.55 * cm,
        topMargin=1.25 * cm,
        bottomMargin=1.45 * cm,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="normal",
        showBoundary=0,
    )
    doc.addPageTemplates([PageTemplate(id="cv", frames=[frame], onPage=header)])

    story = []
    story.append(para("SYED MUHAMMAD AHMAD BOKHARI", "Name"))
    story.append(para("Graduate Business Analyst | Business Systems, Data Quality and Digital Transformation", "Role"))
    story.append(
        para(
            "Bradford, UK | 07769685019 | bokhariahmed765@gmail.com | linkedin.com/in/syed-muhammad-ahmad-bokhari-aa5064294 | github.com/syedahmadbokhari",
            "Tight",
        )
    )

    add_section(story, "Profile")
    story.append(
        para(
            "First-Class BSc Applied Artificial Intelligence graduate with hands-on experience turning messy operational data into documented workflows, tested pipelines, dashboards and stakeholder-ready reporting. Strong fit for a Graduate Business Analyst role across business systems and transformation: requirements clarification, process/data mapping, functional documentation, data validation, testing, Excel/reporting and cross-functional communication. Project background spans retail, public-sector operations, crime data and AI monitoring, with particular interest in ERP, PLM/MES-connected data flows, BoMs/product structures and continuous process improvement.",
            "Body",
        )
    )

    add_section(story, "Role-Relevant Skills")
    story.append(
        bullet_list(
            [
                "Business analysis: requirements gathering, process mapping, user stories, functional documentation, stakeholder reporting and issue/risk communication.",
                "Business systems and data: SQL, PostgreSQL, DuckDB, dbt, Airflow, FastAPI, Docker, BigQuery, Snowflake concepts, data integration and pipeline orchestration.",
                "Reporting and analysis: Excel, Power BI, Tableau, Streamlit, KPI dashboards, variance analysis, cohort/trend analysis and plain-language summaries.",
                "Testing and assurance: UAT-style scenario checks, pytest, dbt schema tests, Great Expectations, data migration validation, reconciliation and data integrity controls.",
                "Working style: structured, detail-focused, proactive learner comfortable translating between technical teams and non-technical stakeholders.",
            ]
        )
    )

    add_section(story, "Education")
    story.append(para("<b>BSc (Hons) Applied Artificial Intelligence - University of Bradford</b> | 2023 - 2026", "Tight"))
    story.append(para("First Class Honours. Relevant areas: databases, machine learning, software engineering, data analysis, AI systems and project delivery.", "Body"))

    add_section(story, "Selected Projects")
    add_project(
        story,
        "AI Interview Prep Assistant - RAG Business Knowledge System",
        "Python, FastAPI, React, FAISS, MiniLM, Groq, JWT, Docker, Render",
        [
            "Built a deployed question-answering system over real project documentation, converting project knowledge into a searchable business support workflow with grounded citations and honest refusals.",
            "Documented architecture, configuration, security tradeoffs, API behaviour and error contracts so users and reviewers could understand how the system works end to end.",
            "Implemented JWT-protected FastAPI endpoints, rate limiting, validation and React UI states, then verified the live flow with E2E checks covering login, grounded answers and refusal handling.",
            "Strong match to business systems work: requirements-to-workflow translation, user-facing documentation, test scenarios, data retrieval logic and controlled system adoption.",
        ],
    )
    add_project(
        story,
        "UK Crime Data Pipeline - Public Sector Data Integration and Reporting",
        "Python, S3, DuckDB, dbt, Airflow, FastAPI, Great Expectations, Kafka, Streamlit, Terraform",
        [
            "Designed an end-to-end monthly data pipeline for UK Police open data: ingestion, warehouse loading, dbt staging/marts, data quality gates, dashboarding and API access.",
            "Mapped operational data flows from source CSVs through raw, clean and mart layers, using watermarks and idempotent loading to avoid duplicate or missed records.",
            "Added formal Great Expectations checks for schema, nulls, accepted values, coordinate ranges and crime ID uniqueness, strengthening process compliance and data integrity.",
            "Produced stakeholder-focused dashboards for trends, category breakdowns, hotspots and force KPIs, translating technical outputs into operational insight.",
        ],
    )
    add_project(
        story,
        "Retail Data Platform - Analytics, Data Quality and Business Reporting",
        "SQL, Python, PostgreSQL, dbt, Airflow, Docker, Excel, Power BI, Tableau, Streamlit",
        [
            "Built a production-style retail analytics platform with incremental event processing, raw/clean/analytics layers, dbt transformations and Airflow orchestration.",
            "Created Power BI, Tableau, Streamlit and Excel reporting outputs covering revenue, discount impact, traffic trends, product performance and pricing opportunities.",
            "Identified and handled 354 corrupted GBP 0 price records before feature engineering, preventing downstream reporting and recommendation outputs from being distorted.",
            "Used statistical testing and BigQuery dry-run analysis to validate findings and optimise query design, including a verified 58.7% bytes-scanned reduction.",
        ],
    )

    story.append(PageBreak())
    add_section(story, "Selected Projects Continued")
    add_project(
        story,
        "AI for Environmental Monitoring and Urban Planning - Final-Year Project",
        "Python, OpenCV, PyTorch, MobileNetV3, ByteTrack, YOLOv8, Flask, GIS",
        [
            "Delivered a real-time illegal dumping detection system over 5.5 months using CDIO and Agile across eight prototype versions.",
            "Created a live monitoring dashboard with alerts, snapshots, confidence scores and GIS hotspot mapping, helping stakeholders assess events rather than raw model output.",
            "Reported sensitivity and false-positive tradeoffs clearly, designing an officer-in-the-loop feedback flow where dismissed alerts become future retraining data.",
            "Produced project documentation and evaluation evidence against manually observed ground truth: 75% accuracy and 60% recall on event-based metrics.",
        ],
    )
    add_project(
        story,
        "Retail / Market Intelligence SQL Analytics",
        "SQL, Python, DuckDB, dbt, Power BI, Streamlit",
        [
            "Analysed performance across 43 organisations using SQL CTEs and window functions, surfacing trends, seasonal patterns, geographic variance and risks.",
            "Built self-serve dashboards and plain-language summaries so non-technical users could explore results and act on the findings.",
            "Used dbt/Python modelling to structure repeatable analytics tables, aligning technical data transformation with business reporting needs.",
        ],
    )

    add_section(story, "Experience")
    story.append(para("<b>AI Project Lead, Bradford Council</b> | Jul 2026 - Present", "Subhead"))
    story.append(
        bullet_list(
            [
                "Leading a data-driven AI monitoring project for a local council, translating detection outputs into stakeholder reporting and practical operational workflows.",
                "Coordinating requirements, reporting cadence and progress updates with Council and academic stakeholders within governance and data protection constraints.",
                "Leading a team of three across an estimated six-month engagement, using fortnightly reporting to manage priorities, surface risks and maintain delivery momentum.",
            ]
        )
    )

    add_section(story, "Technical Toolkit")
    story.append(
        para(
            "<b>Analysis and reporting:</b> Excel, Power BI, Tableau, Streamlit, KPI dashboards, SQL reporting, stakeholder summaries.",
            "Tight",
        )
    )
    story.append(
        para(
            "<b>Data and systems:</b> Python, SQL, PostgreSQL, DuckDB, dbt, Airflow, FastAPI, Docker, BigQuery, Snowflake concepts, S3, Kafka concepts.",
            "Tight",
        )
    )
    story.append(
        para(
            "<b>Quality and delivery:</b> pytest, dbt tests, Great Expectations, GitHub Actions, data validation, reconciliation, documentation, Agile/CDIO.",
            "Body",
        )
    )

    add_section(story, "Certifications")
    story.append(para("IBM SkillsBuild - Data Fundamentals and AI Fundamentals Certificates (2026)", "Body"))

    add_section(story, "Additional Fit for Graduate Business Analyst Role")
    story.append(
        bullet_list(
            [
                "Keen to develop hands-on experience with ERP platforms, PLM/MES/WMS integrations, BoMs, product structures and manufacturing-focused digital transformation.",
                "Comfortable learning new business systems quickly and documenting workflows, test outcomes, user requirements and training guidance in clear language.",
                "Strong attention to data accuracy, process compliance and continuous improvement, with repeated project evidence of validating data before it reaches dashboards or users.",
            ]
        )
    )

    doc.build(story)
    print(OUT)


if __name__ == "__main__":
    build()
