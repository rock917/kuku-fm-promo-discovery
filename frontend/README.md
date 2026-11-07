# Kuku FM — Promo Discovery Web UI

Frontend dashboard for Kuku FM's AI Generalist Assignment (Problem 1: Find the Promos).  
Designed for **Vercel deployment** with an **Azure App Service FastAPI Backend**.

---

## Features

- **Ranked Promos Explorer**:
  - Filter by Episode, Minimum Score, and Duration.
  - Verbatim **Opening Hook** (first 3s callout) & **Closing Cliffhanger** (unresolved peak).
  - Standalone Narrative Context explanation.
  - **Explainable 5-Dimension Score Breakdown**:
    - ⚡ AI: Hook Strength (25%)
    - ⚡ AI: Cliffhanger Strength (30%)
    - ⚡ AI: Standalone Clarity (20%)
    - ⚡ AI: Emotional Impact (15%)
    - 🔒 Programmatic: Duration Quality (10%)
  - One-click export to JSON and CSV.
- **Quality & Validation Dashboard**:
  - Total candidate counts (218 generated, 122 valid, 96 duplicates/disqualified).
  - Validation constraint audit (0 timestamp errors, 0 hallucinated dialogue errors).
  - Episode coverage metrics (50/50 episodes).
- **Failure Analysis & System Limitations**:
  - Honest audit of 6 documented system limitations and engineering mitigations.
  - Full inspection of disqualified candidates and reasons.
- **Source Screenplay Traceability Viewer**:
  - Direct raw text viewer for all 50 episodes with scene-relative timestamp notes.
- **Pipeline Controls**:
  - Trigger runs with Groq, Gemini, OpenAI, or Mock.
- **Dual Mode (Azure Live API + Vercel Bundled Fallback)**:
  - If the Azure API is connected, live calls are made.
  - If deployed standalone on Vercel without a backend yet, bundled pipeline outputs load instantly!

---

## Local Development

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

---

## Deploy to Vercel

### Method 1: Vercel CLI
```bash
cd frontend
vercel
```

### Method 2: Git Integration
1. Push your repository to GitHub / GitLab.
2. In the Vercel dashboard, click **Add New Project** and select this repo.
3. Set the **Root Directory** to `frontend`.
4. (Optional) In **Environment Variables**, set:
   ```
   VITE_API_URL=https://<your-azure-app-service>.azurewebsites.net
   ```
5. Click **Deploy**!
