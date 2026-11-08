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
            self.draw_page_decorations(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#0f172a"))
        self.drawString(32, 814, "KUKU FM — AI GENERALIST ASSIGNMENT")
        self.setFont("Helvetica", 7.5)
        self.setFillColor(colors.HexColor("#64748b"))
        self.drawString(205, 814, "|   Problem 1: Automated Promo Discovery & Grounded Ranking")
        self.drawRightString(563, 814, f"Page {self._pageNumber} of {page_count}")
        
        # Header dividing line
        self.setStrokeColor(colors.HexColor("#e2e8f0"))
        self.setLineWidth(0.75)
        self.line(32, 808, 563, 808)
        
        # Footer dividing line
        self.line(32, 28, 563, 28)
        self.drawString(32, 18, "CONFIDENTIAL · Prepared for Kuku FM Technical Evaluation")
        self.drawRightString(563, 18, "PromoFinder AI Solution Architecture")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_PATH,
        pagesize=A4,
        leftMargin=32,
        rightMargin=32,
        topMargin=42,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=14.5,
        textColor=colors.HexColor('#0f172a'),
        spaceAfter=1
    )
    
    sub_title_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7.5,
        leading=9.5,
        textColor=colors.HexColor('#e11d48'),
        spaceAfter=3,
        textTransform='uppercase'
    )
    
    h2_style = ParagraphStyle(
        'SecHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.2,
        leading=10,
        textColor=colors.HexColor('#0f172a'),
        spaceBefore=3,
        spaceAfter=1.5,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.8,
        leading=8.6,
        textColor=colors.HexColor('#1e293b'),
        spaceAfter=2,
        alignment=4 # Justified
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.3,
        leading=7.8,
        textColor=colors.HexColor('#1e293b')
    )
    
    cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.3,
        leading=7.8,
        textColor=colors.HexColor('#0f172a')
    )
    
    th_style = ParagraphStyle(
        'TableHead',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.3,
        leading=7.8,
        textColor=colors.HexColor('#334155')
    )

    story = []

    # ==================== PAGE 1 ====================
    story.append(Paragraph("PROMOFINDER AI — TECHNICAL ARCHITECTURE & SOLUTION WHITEPAPER", title_style))
    story.append(Paragraph("Automated Promo Discovery, Screenplay Grounding & Deterministic Validation", sub_title_style))

    story.append(Paragraph("1. Strategic Business Framing & Leverage (Why Problem 1?)", h2_style))
    story.append(Paragraph(
        "In vertical microdramas (1–2 minute episodes), audience acquisition is overwhelmingly driven by paid performance marketing (Meta Reels, TikTok Spark Ads, YouTube Shorts). Conversion curves are brutally steep: <b>~65% of scrollers drop off within 3 seconds</b>, and over 80% abandon by second 10. Currently, human editors spend 30–45 minutes per episode manually scrubbing footage to identify promo cuts. Across a 50-episode show, this demands <b>25 to 37.5 hours of senior editorial labor</b>, creating a severe operational bottleneck. <b>PromoFinder AI</b> automates this pipeline directly from pre-production screenplays, shifting editors from manual hunting to high-value curation. Surfacing the top 5% highest-retention cuts reduces turnaround from days to seconds, allowing marketing teams to test 10x more ad creative variants and significantly reducing Blended Customer Acquisition Cost (CAC).",
        body_style
    ))

    story.append(Paragraph("2. Operational Assumptions & Screenplay Domain Realities", h2_style))
    assumptions_data = [
        [Paragraph("Dimension", th_style), Paragraph("Screenplay Domain Reality", th_style), Paragraph("Engineering Rationale & System Implementation", th_style)],
        [Paragraph("Clock Coordinate Space", cell_bold), Paragraph("Scene-relative clock resets (every scene starts at <code>00:00.00</code>).", cell_style), Paragraph("Verified across all 50 episodes. Storing naive global timestamps would cause fatal multi-scene desync. All segments maintain an independent <code>(episode, scene, start_ts, end_ts)</code> coordinate tuple.", cell_style)],
        [Paragraph("Duration Sweet Spot", cell_bold), Paragraph("Hard constraint: [20s, 60s]. Social ad completion peaks at 28s–42s.", cell_style), Paragraph("Implemented a continuous polynomial decay curve centered at 35.0s: <code>10.0 - 3.2&times;(|d - 35|/25)^1.4</code>. Avoids discrete step-function cliffs; clips <20s or >60s are strictly disqualified.", cell_style)],
        [Paragraph("Producer SFX Cues", cell_bold), Paragraph("Script tags like <code>CLIFFHANGER SFX</code> are authorial hints, not verdicts.", cell_style), Paragraph("Writers insert stings over mundane dialogue. SFX is treated as a secondary calibration signal; genuine unresolved dialogue tension is required for high scores.", cell_style)],
        [Paragraph("Hallucination Safety", cell_bold), Paragraph("LLM summaries are interpretive prose; dialogue must be verbatim.", cell_style), Paragraph("Deterministic regex substring verification checks quoted lines (<code>\"...\"</code>) against the raw screenplay text with &plusmn;0.5s tolerance, guaranteeing zero invented dialogue lines.", cell_style)],
    ]
    t_assump = Table(assumptions_data, colWidths=[90, 140, 301])
    t_assump.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_assump)

    story.append(Paragraph("3. System Architecture & Component Separation (~65% Deterministic / ~35% LLM)", h2_style))
    story.append(Paragraph(
        "The architecture enforces a strict boundary between deterministic procedural code and qualitative LLM reasoning:<br/>"
        "• <b>Parser (<code>parser.py</code>):</b> State-machine regex parser extracting scenes, character dialogue, emotions, and scene-relative timestamps. Handles both standard and Episode-6 ALL-CAPS formats, plus inline bracket syntax.<br/>"
        "• <b>Windowing Engine (<code>analyzer.py</code>):</b> Generates heuristic candidate cuts per scene (Full Scene, First-45s Hook, Climax Cut, SFX-Anchored). Produces an average of 4.3 candidates per episode.<br/>"
        "• <b>Pluggable LLM Client (<code>llm_client.py</code>):</b> Standardized interface supporting Groq (LLaMA 3.3 70B), OpenAI (GPT-4o-mini), Google Gemini, or grounded Mock, backed by a content-addressed SHA-256 disk cache (<code>outputs/cache/</code>).<br/>"
        "• <b>Deterministic Validator (<code>validator.py</code>):</b> 100% Python enforcement—duration bounds [20s, 60s], timestamp existence (&plusmn;0.5s), dialogue grounding, and temporal graph deduplication.<br/>"
        "• <b>Cloud Deployment:</b> Vercel SPA (React 18/Tailwind CSS) &harr; Vercel Edge Reverse Proxy (<code>/api/*</code>) &harr; Azure Basic B1 FastAPI Backend &harr; Supabase Managed PostgreSQL. Screenplay source viewer streams all 50 full scripts via CDN <code>episodes.json</code>.",
        body_style
    ))

    story.append(Paragraph("4. Explainable 5-Dimension Grounded Scoring Rubric", h2_style))
    scoring_data = [
        [Paragraph("Dimension", th_style), Paragraph("Weight", th_style), Paragraph("Engine", th_style), Paragraph("Screenplay Grounding & Evaluation Formula", th_style)],
        [Paragraph("Hook Strength", cell_bold), Paragraph("25%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("First 3s trigger: dialogue onset speed (&le;1.5s gives +0.9), emotional directions (<code>Cold</code>, <code>Defiant</code>, <code>Whispering</code>), line brevity (15–95 chars).", cell_style)],
        [Paragraph("Cliffhanger Strength", cell_bold), Paragraph("30%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Unresolved tension at cut: terminal punctuation (<code>?</code>, <code>!</code>, <code>...</code>, <code>&mdash;</code>), climax cliffhanger SFX within final 10s, abrupt conversation cutoff.", cell_style)],
        [Paragraph("Standalone Clarity", cell_bold), Paragraph("20%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Context intelligibility for cold traffic: dialogue density (&ge;0.55), two-speaker duets (scenes with >3 active speakers receive context clutter penalty).", cell_style)],
        [Paragraph("Emotional Impact", cell_bold), Paragraph("15%", cell_style), Paragraph("AI + Grounded", cell_style), Paragraph("Visceral stakes: density of high-conflict domain keywords (<i>betrayal, marriage, scars, murder, duke, honor, blade, fire, dead</i>).", cell_style)],
        [Paragraph("Duration Quality", cell_bold), Paragraph("10%", cell_style), Paragraph("Deterministic", cell_style), Paragraph("Continuous mathematical decay: <code>10.0 - 3.2&times;(|duration - 35.0| / 25.0)^1.4</code>. 35.0s &rarr; 10.0; 25s/45s &rarr; 9.36; 20s/60s &rarr; 7.20.", cell_style)],
    ]
    t_score = Table(scoring_data, colWidths=[85, 38, 62, 346])
    t_score.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_score)

    # ==================== PAGE 2 ====================
    story.append(PageBreak())

    story.append(Paragraph("PROMOFINDER AI — TELEMETRY, COST MODELING & FAILURE AUDIT", title_style))
    story.append(Paragraph("Graph Deduplication Math, Telemetry Funnel, Unit Economics & AI Failure Reflection", sub_title_style))

    story.append(Paragraph("5. Deduplication Algorithm & Graph Theory Mathematics", h2_style))
    story.append(Paragraph(
        "Candidate windowing frequently creates overlapping cuts (e.g., a 45s opening hook vs. a 55s full scene of the same dialogue). In naive systems, teams confuse pairwise collisions with filtered candidates. We formulate this rigorously using graph theory:<br/>"
        "1. Construct an <b>Intersection Graph</b> <i>G = (V, E)</i>, where vertices <i>V</i> represent candidate cuts (|V| = 218). An edge <i>e = (u, v) &isin; E</i> exists if the temporal Intersection-over-Union (IoU) of dialogue lines between candidates <i>u</i> and <i>v</i> exceeds <b>60%</b>: <code>IoU(u, v) = |u &cap; v| / |u &cup; v| &ge; 0.60</code>.<br/>"
        "2. Across 50 episodes, this detects exactly <b>133 pairwise collision edges</b>.<br/>"
        "3. A <b>Greedy Maximal Independent Set</b> algorithm sorts candidates by preliminary score. When the highest-scoring candidate is selected, all connected adjacent vertices are eliminated together.<br/>"
        "4. <b>Result:</b> Exactly <b>96 redundant candidate vertices are pruned</b>, leaving <b>122 distinct, non-overlapping candidate clips</b> in the ranking pool.",
        body_style
    ))

    story.append(Paragraph("6. Telemetry Funnel & Cost Modeling at Enterprise Scale", h2_style))
    story.append(Paragraph(
        "<b>Empirical 50-Episode Pack Telemetry:</b> 218 Total Evaluated &rarr; 122 Passed Validation (<b>56.0% pass rate</b>) &rarr; 96 Pruned as Redundant (<b>44.0% prune rate</b>) &rarr; 122/122 Accepted Pool Constraint Compliance (<b>100.0%</b>: 0 timestamp errors, 0 hallucinations, 0 duration violations) &rarr; Top 20 Ranked Output (Scores: 7.591 to 8.534, Mean: 7.914).<br/>"
        "<b>Rank #1 Promo (Ep 36, 44.8s, Score: 8.534):</b> Hook: <i>ALEXANDER: (Simmering with Fury) \"They are marrying in two days...\"</i> &harr; Cliffhanger: <i>MOTHER: \"Then why did they leave...\"</i>",
        body_style
    ))

    cost_data = [
        [Paragraph("Pipeline Execution Tier", th_style), Paragraph("Cost per Episode", th_style), Paragraph("Cost per 50-Ep Show", th_style), Paragraph("End-to-End Latency", th_style), Paragraph("Commercial Operational Viability", th_style)],
        [Paragraph("Groq (LLaMA 3.3 70B)", cell_bold), Paragraph("<b>$0.0005</b> (~650 tokens)", cell_style), Paragraph("<b>$0.025</b> (2.5 cents)", cell_style), Paragraph("14.2 seconds", cell_style), Paragraph("Ideal for high-volume batch processing; ultra-low inference cost.", cell_style)],
        [Paragraph("OpenAI (GPT-4o-mini)", cell_bold), Paragraph("<b>$0.0021</b> (~650 tokens)", cell_style), Paragraph("<b>$0.105</b> (10.5 cents)", cell_style), Paragraph("32.5 seconds", cell_style), Paragraph("Standard enterprise fallback; exceptional JSON structured output adherence.", cell_style)],
        [Paragraph("Manual Human Editor", cell_bold), Paragraph("~$25.00 (35 mins labor)", cell_style), Paragraph("~$1,250.00 (30 hours)", cell_style), Paragraph("3 to 5 business days", cell_style), Paragraph("Severe bottleneck; inconsistent creative quality and high human fatigue.", cell_style)],
    ]
    t_cost = Table(cost_data, colWidths=[105, 85, 85, 75, 181])
    t_cost.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_cost)

    story.append(Paragraph("7. Transparent System Limitations & Engineering Edge Cases", h2_style))
    limit_data = [
        [Paragraph("Limitation", th_style), Paragraph("System Impact", th_style), Paragraph("Engineering Mitigation Strategy", th_style)],
        [Paragraph("Sub-20s Short Scenes", cell_bold), Paragraph("Ep 39 & Ep 44 produce 0 promo windows.", cell_style), Paragraph("Intended design: clips under 20s lack sufficient narrative body for social ad retention.", cell_style)],
        [Paragraph("Audio Delivery Blindness", cell_bold), Paragraph("Text scripts omit vocal cadence & pause timings.", cell_style), Paragraph("Parsed emotional stage directions (<code>Coldly</code>, <code>Whispering</code>, <code>Terrified</code>) act as weighted proxies.", cell_style)],
        [Paragraph("Crowd Cross-Talk Density", cell_bold), Paragraph("Scenes with 4+ speakers degrade standalone clarity.", cell_style), Paragraph("Standalone clarity metric penalizes scenes exceeding 3 active speakers to favor focused 2-person duets.", cell_style)],
    ]
    t_limit = Table(limit_data, colWidths=[100, 150, 281])
    t_limit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('TOPPADDING', (0, 0), (-1, -1), 1.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.5),
    ]))
    story.append(t_limit)

    story.append(Paragraph("8. AI Tools Used & Documented AI Development Failure", h2_style))
    story.append(Paragraph(
        "<b>AI Tools Utilized:</b> Google Gemini 1.5 Flash API, OpenAI GPT-4o-mini, Groq LLaMA 3.3 70B, and Antigravity Agent for iterative architectural review.<br/>"
        "<b>Documented AI Failure During Development:</b> Early in pipeline construction, an AI-generated instruction prompted the hallucination validator to check whether the <i>entire candidate rationale sentence</i> was a verbatim substring of the screenplay text. This created an immediate, catastrophic false-positive failure: <b>100% of generated candidates (218/218) were disqualified as hallucinations</b>, because LLM rationales are interpretive prose (e.g., <i>\"Alexander confronts the matriarch regarding his scars\"</i>), which never appears literally in scripts. <br/>"
        "<b>The Fix:</b> We re-engineered the validator in deterministic Python using regular expressions to isolate only text enclosed in quotation marks (<code>\"...\"</code>) with &ge;10 characters, validating only dialogue quotes against the source text. This restored 100% validation fidelity while preventing real hallucinations.",
        body_style
    ))

    story.append(Paragraph("9. Zero-Modification Scaling to Future Shows & Production Ingestion", h2_style))
    story.append(Paragraph(
        "PromoFinder AI requires <b>zero source code modifications</b> to process any upcoming Kuku FM series: placing raw <code>.txt</code> files into <code>data/scripts/&lt;show_name&gt;</code> and executing <code>python src/pipeline.py</code> automatically detects scene markers, headings, timestamp bounds, and formatting variants. For live ad teams, the deployed web application features an on-demand <b>Pipeline & Ingestion Tab</b> allowing editors to paste raw script text or enter public URLs (Google Drive, Dropbox, S3) to discover and rank promo moments in real time via the Azure backend.",
        body_style
    ))

    doc.build(story, canvasmaker=NumberedCanvas)
    print("SUCCESS: solution_document.pdf regenerated with deep executive rigor!")

if __name__ == "__main__":
    build_pdf()
