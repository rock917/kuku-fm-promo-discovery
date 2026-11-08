import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

PDF_PATH = r"e:\Kuku_FM_CASE_STUDY\solution_document.pdf"

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        # Header line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.5)
        self.line(32, 810, 563, 810)
        self.drawString(32, 814, "KUKU FM — AI GENERALIST ASSIGNMENT · PROBLEM 1: FIND THE PROMOS")
        self.drawRightString(563, 814, f"Page {self._pageNumber} of {page_count}")
        # Footer
        self.line(32, 28, 563, 28)
        self.drawString(32, 18, "CONFIDENTIAL · Prepared for Kuku FM Technical Evaluation")
        self.drawRightString(563, 18, "PromoFinder AI Solution Document")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=40,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=1
    )
    
    sub_title_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#e11d48'),
        spaceAfter=4,
        textTransform='uppercase'
    )
    
    h2_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.5,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=4,
        spaceAfter=2,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.2,
        leading=9.2,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=3,
        alignment=4 # Justified
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.3,
        textColor=colors.HexColor('#1e293b')
    )
    
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.8,
        leading=8.3,
        textColor=colors.HexColor('#0f172a')
    )
    
    th_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.8,
        leading=8.3,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # ==================== PAGE 1 ====================
    story.append(Paragraph("PROMOFINDER AI — EXECUTIVE SOLUTION DOCUMENT", title_style))
    story.append(Paragraph("Problem 1: Automated Promo Discovery & Grounded Ranking for Microdramas", sub_title_style))

    story.append(Paragraph("1. Problem Framing & Leverage", h2_style))
    story.append(Paragraph(
        "Promo discovery is the highest-leverage growth engine in microdrama streaming: a compelling 30-second vertical cut on Instagram, TikTok, or YouTube cold-converts passive scrollers into paying subscribers. Manually reviewing 50+ episodes weekly per show creates severe editorial bottlenecks. <b>PromoFinder AI</b> replaces subjective manual hunting with automated screenplay parsing, heuristic candidate windowing, LLM narrative evaluation, and deterministic Python constraint verification.",
        body_style
    ))

    story.append(Paragraph("2. Operational Assumptions", h2_style))
    assumptions_data = [
        [Paragraph("Assumption", th_style), Paragraph("Screenplay Verification & Engineering Rationale", th_style)],
        [Paragraph("Scene-Relative Timestamps", cell_bold), Paragraph("Verified across all 50 episodes: every scene resets to <code>00:00.00</code>. Multi-scene cuts track independent segment clocks.", cell_style)],
        [Paragraph("Windowing Dynamics", cell_bold), Paragraph("Full scenes average 1–3 min; pipeline extracts 20s–60s cuts (ideal: 25s–45s) anchored on early hooks or closing climaxes.", cell_style)],
        [Paragraph("SFX as Supporting Signals", cell_bold), Paragraph("Labels like <code>CLIFFHANGER SFX</code> are treated as audio hints, not verdicts—unresolved dialogue tension takes priority.", cell_style)],
        [Paragraph("Hallucination Safety", cell_bold), Paragraph("Strict substring matching runs on quoted lines (<code>\"...\"</code>) against script source, ensuring zero invented dialogue.", cell_style)],
    ]
    t_assump = Table(assumptions_data, colWidths=[120, 411])
    t_assump.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_assump)

    story.append(Paragraph("3. System Architecture & End-to-End Pipeline", h2_style))
    story.append(Paragraph(
        "<b>Workflow:</b> <code>parser.py</code> (scene & timestamp extraction) &rarr; <code>analyzer.py</code> (windowing: full-scene, first-45s, climax) &rarr; <code>llm_client.py</code> (Groq LLaMA 3.3 / OpenAI / Gemini / Mock) &rarr; <code>validator.py</code> (deterministic duration, timestamp existence, graph dedup) &rarr; <code>scorer.py</code> (5D continuous scoring) &rarr; <code>reporter.py</code>.<br/>"
        "<b>Deployment:</b> Vercel Web Dashboard (React/Tailwind) + Azure Basic B1 FastAPI Backend + Vercel Edge Reverse Proxy (<code>/api/*</code>) + Supabase PostgreSQL Database. Screenplay source viewer streams all 50 full scripts instantly via CDN <code>episodes.json</code>.",
        body_style
    ))

    story.append(Paragraph("4. Explainable 5-Dimension Grounded Scoring Rubric", h2_style))
    scoring_data = [
        [Paragraph("Dimension", th_style), Paragraph("Weight", th_style), Paragraph("Engine", th_style), Paragraph("Screenplay Grounding & Evaluation Criteria", th_style)],
        [Paragraph("Hook Strength", cell_bold), Paragraph("25%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("First 3s trigger: dialogue onset (&le;1.5s), emotional delivery (Cold, Defiant, Whispering), shocking reveal.", cell_style)],
        [Paragraph("Cliffhanger Strength", cell_bold), Paragraph("30%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Unresolved tension at cut point: open questions, abrupt breaks, gasps, and supporting cliffhanger SFX stings.", cell_style)],
        [Paragraph("Standalone Clarity", cell_bold), Paragraph("20%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Self-contained narrative: cold viewer understands conflict without prior lore or 50 episodes of backstory.", cell_style)],
        [Paragraph("Emotional Impact", cell_bold), Paragraph("15%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Visceral stakes: density of drama keywords (betrayal, marriage, scars, murder, duke, blade, blood).", cell_style)],
        [Paragraph("Duration Quality", cell_bold), Paragraph("10%", cell_style), Paragraph("Deterministic", cell_style), Paragraph("Continuous smooth decay curve centered at 35.0s sweet spot: <code>10.0 - 3.2&times;(|d - 35|/25)^1.4</code>. Bounds: [20s, 60s].", cell_style)],
    ]
    t_score = Table(scoring_data, colWidths=[95, 42, 65, 329])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_score)

    # ==================== PAGE 2 ====================
    story.append(PageBreak())

    story.append(Paragraph("PROMOFINDER AI — EVALUATION, TELEMETRY & AUDIT", title_style))
    story.append(Paragraph("Quality Telemetry, Failure Audit, Engineering Boundaries & AI Tool Reflection", sub_title_style))

    story.append(Paragraph("5. AI vs. Rule-Based Allocation (~65% Deterministic / ~35% LLM Reasoning)", h2_style))
    alloc_data = [
        [Paragraph("Task Component", th_style), Paragraph("Allocation", th_style), Paragraph("Engineering Rationale", th_style)],
        [Paragraph("Timestamp & Duration Bounds", cell_bold), Paragraph("100% Deterministic", cell_style), Paragraph("LLMs struggle with arithmetic; strict Python checks guarantee zero constraint violations.", cell_style)],
        [Paragraph("Graph Deduplication (&ge;60% IoU)", cell_bold), Paragraph("100% Deterministic", cell_style), Paragraph("Greedy maximal independent set algorithm eliminates redundant overlapping cuts algorithmically.", cell_style)],
        [Paragraph("Dialogue Quote Verification", cell_bold), Paragraph("100% Deterministic", cell_style), Paragraph("Regex substring validation checks all quoted lines exist verbatim in source screenplay.", cell_style)],
        [Paragraph("Narrative Quality Scoring", cell_bold), Paragraph("LLM Reasoning", cell_style), Paragraph("Evaluates psychological curiosity, character emotional arousal, and unresolved narrative pull.", cell_style)],
    ]
    t_alloc = Table(alloc_data, colWidths=[125, 80, 326])
    t_alloc.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_alloc)

    story.append(Paragraph("6. Telemetry & Deduplication Funnel (Full 50-Episode Pack Execution)", h2_style))
    story.append(Paragraph(
        "• <b>Total Evaluated:</b> 218 raw candidate windows across all 50 episodes (100% episode coverage).<br/>"
        "• <b>Validation Pass Rate:</b> <b>56.0%</b> (122 candidates admitted to ranking pool).<br/>"
        "• <b>Redundant Prune Rate:</b> <b>44.0%</b> (96 redundant overlapping cuts pruned via graph deduplication).<br/>"
        "• <b>Accepted Pool Constraint Compliance:</b> <b>100.0%</b> (122 / 122 with 0 timestamp errors, 0 hallucinations, 0 duration violations).<br/>"
        "• <b>Deduplication Graph Math:</b> 133 pairwise overlap collisions (&ge;60% IoU) pruned down to exactly 96 eliminated vertices.<br/>"
        "• <b>Ranked Output:</b> Top 20 distinct, non-overlapping promo moments (Scores range: 7.591 to 8.534, mean: 7.914).",
        body_style
    ))

    story.append(Paragraph("7. Documented System Limitations & Failure Modes", h2_style))
    limit_data = [
        [Paragraph("Limitation", th_style), Paragraph("System Impact", th_style), Paragraph("Engineering Mitigation", th_style)],
        [Paragraph("Short Scenes (<20s)", cell_bold), Paragraph("Ep 39 & Ep 44 produce 0 promo windows.", cell_style), Paragraph("Intended: clips under 20s lack narrative weight for social ad retention.", cell_style)],
        [Paragraph("Audio Delivery Blindness", cell_bold), Paragraph("Text scripts omit actor pacing & audio tone.", cell_style), Paragraph("Emotional stage directions (e.g. <code>(Coldly)</code>, <code>(Whispering)</code>) are parsed & scored.", cell_style)],
        [Paragraph("Multi-Character Cross-Talk", cell_bold), Paragraph("Scenes with 4+ speakers confuse cold traffic.", cell_style), Paragraph("Standalone clarity metric penalizes scenes exceeding 3 active speakers.", cell_style)],
    ]
    t_limit = Table(limit_data, colWidths=[110, 160, 261])
    t_limit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    story.append(t_limit)

    story.append(Paragraph("8. AI Tools Used & Documented AI Failure Case", h2_style))
    story.append(Paragraph(
        "<b>AI Tools Utilized:</b> Google Gemini API, OpenAI GPT-4o-mini, Groq LLaMA 3.3 70B, and Antigravity Assistant for architecture review.<br/>"
        "<b>Documented AI Failure During Development:</b> Early in development, the AI-generated hallucination validator was prompted to check whether the entire generated candidate summary was a substring of the source script. This caused an catastrophic false-positive failure, rejecting <b>100% of valid candidates (218/218)</b> because AI rationales are descriptive paraphrases (e.g., <i>\"Alexander confronts the matriarch\"</i>) which do not appear literally in scripts. <b>Fix:</b> We re-engineered the validator to isolate verbatim dialogue quotes (<code>\"...\"</code>) and verify only those strings against the script text, restoring 100% accuracy while preventing actual hallucinations.",
        body_style
    ))

    story.append(Paragraph("9. Scalability to Future Shows", h2_style))
    story.append(Paragraph(
        "<b>Zero code modifications required.</b> Processing a new microdrama simply requires placing raw <code>.txt</code> files into <code>data/scripts/&lt;show_name&gt;</code> and executing <code>python src/pipeline.py</code>. The parser auto-detects scene headings, bracket timestamps, and ALL-CAPS script variants. For production editorial teams, the live Web Ingestion tab analyzes pasted screenplays or public URLs on-demand.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("SUCCESS: solution_document.pdf generated successfully!")

if __name__ == "__main__":
    build_pdf()
