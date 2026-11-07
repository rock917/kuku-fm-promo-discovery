# =============================================================================
# app.py — Kuku FM Promo Discovery System · Streamlit UI
#
# Tabs:
#   1. 🏆 Ranked Promos   — browse, filter, inspect with score breakdown
#   2. 📋 Quality Report  — pipeline stats, failure type distribution
#   3. ⚠️  Failure Analysis — documented system limitations + invalid candidates
#   4. 📖 Source Viewer   — trace any promo back to raw screenplay text
#   5. ⚙️  Run Pipeline    — trigger a fresh analysis run from the UI
#
# AI-generated scores are clearly distinguished from programmatic constraints.
# =============================================================================

from __future__ import annotations

import json
import csv
import io
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT       = Path(__file__).parent.parent
OUTPUTS    = ROOT / "outputs"
SCRIPTS    = ROOT / "data" / "scripts" / "I Married a Broken Soldier. He was a Duke"
PROMOS_JSON     = OUTPUTS / "promos.json"
PROMOS_CSV      = OUTPUTS / "promos.csv"
QUALITY_JSON    = OUTPUTS / "quality_report.json"
FAILURE_JSON    = OUTPUTS / "failure_analysis.json"

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Kuku FM · Promo Discovery",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
.metric-card {
    background: #1e1e2e;
    border-radius: 8px;
    padding: 12px 16px;
    margin: 4px 0;
}
.score-ai { color: #f8b400; font-weight: 600; }
.score-prog { color: #00c4ff; font-weight: 600; }
.badge-valid { background:#1a7a4a; color:white; padding:2px 8px; border-radius:4px; font-size:0.8em; }
.badge-invalid { background:#8b1a1a; color:white; padding:2px 8px; border-radius:4px; font-size:0.8em; }
.rank-num { font-size:2em; font-weight:800; color:#f8b400; }
div[data-testid="stExpander"] summary { font-size:1.05em; }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Data loaders (cached)
# ---------------------------------------------------------------------------

@st.cache_data(ttl=30)
def load_promos() -> Optional[dict]:
    if not PROMOS_JSON.exists():
        return None
    with open(PROMOS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=30)
def load_quality() -> Optional[dict]:
    if not QUALITY_JSON.exists():
        return None
    with open(QUALITY_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=30)
def load_failure() -> Optional[dict]:
    if not FAILURE_JSON.exists():
        return None
    with open(FAILURE_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


@st.cache_data(ttl=120)
def load_episode_text(episode_number: int) -> str:
    """Return the raw screenplay text for a given episode."""
    for f in SCRIPTS.glob("*.txt"):
        # Match "Episode 1 " prefix (various formats)
        stem = f.stem.lower()
        if f"episode {episode_number} " in stem + " " or f"episode {episode_number:02d} " in stem + " ":
            return f.read_text(encoding="utf-8", errors="replace")
    return f"⚠️ Could not locate script file for Episode {episode_number}."


def clear_cache():
    load_promos.clear()
    load_quality.clear()
    load_failure.clear()
    load_episode_text.clear()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Kuku_FM_Logo.svg/320px-Kuku_FM_Logo.svg.png",
             use_container_width=True)
    st.markdown("## 🎙️ Promo Discovery")
    st.caption("AI-powered promotional moment identification for microdrama screenplays.")
    st.divider()

    data = load_promos()
    if data:
        meta = data.get("metadata", {})
        st.markdown("### Last Run")
        st.markdown(f"**Show:** {meta.get('show','—')}")
        st.markdown(f"**Episodes:** {meta.get('episodes_processed','—')}")
        st.markdown(f"**LLM:** `{meta.get('llm_provider','—')} / {meta.get('llm_model','—')}`")
        st.markdown(f"**Candidates:** {meta.get('total_candidates_generated','—')} → "
                    f"{meta.get('valid_candidates','—')} valid → "
                    f"{meta.get('ranked_output_count','—')} ranked")
        ts = meta.get("generated_at","")
        if ts:
            st.caption(f"Generated: {ts[:19].replace('T',' ')}")
    else:
        st.warning("No pipeline output found. Run the pipeline first.")

    st.divider()
    st.caption("⚡ AI scores = LLM estimates | 🔒 Validation = deterministic Python")

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏆 Ranked Promos",
    "📋 Quality Report",
    "⚠️ Failure Analysis",
    "📖 Source Viewer",
    "⚙️ Run Pipeline",
])


# =============================================================================
# TAB 1 — Ranked Promos
# =============================================================================
with tab1:
    st.title("🏆 Ranked Promo Candidates")
    st.caption(
        "⚡ **AI-generated scores** (hook, cliffhanger, standalone, emotional) come from LLM analysis — "
        "treat as estimates. 🔒 **Programmatic scores** (duration) and all validation checks are "
        "deterministic Python rules."
    )

    data = load_promos()
    if not data:
        st.error("No promo output found. Please run the pipeline first (⚙️ Run Pipeline tab).")
        st.stop()

    promos = data.get("ranked_promos", [])
    if not promos:
        st.warning("No ranked promos in output. Check the Quality Report for validation details.")
        st.stop()

    # --- Filters ---
    with st.expander("🔽 Filters", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            all_eps = sorted({s["episode_number"] for p in promos for s in p["segments"]})
            ep_filter = st.multiselect("Episode", all_eps, placeholder="All episodes")
        with col2:
            min_score = st.slider("Minimum Score", 0.0, 10.0, 0.0, 0.5)
        with col3:
            dur_range = st.slider("Duration (seconds)", 20, 60, (20, 60))

    # Apply filters
    filtered = [
        p for p in promos
        if (not ep_filter or any(s["episode_number"] in ep_filter for s in p["segments"]))
        and (p["final_score"] or 0) >= min_score
        and dur_range[0] <= p["total_duration_sec"] <= dur_range[1]
    ]

    st.markdown(f"**Showing {len(filtered)} of {len(promos)} ranked promos**")

    # --- Export buttons ---
    col_e1, col_e2, _ = st.columns([1, 1, 4])
    with col_e1:
        with open(PROMOS_JSON) as f:
            st.download_button("⬇️ Export JSON", f.read(), file_name="promos.json", mime="application/json")
    with col_e2:
        if PROMOS_CSV.exists():
            with open(PROMOS_CSV) as f:
                st.download_button("⬇️ Export CSV", f.read(), file_name="promos.csv", mime="text/csv")

    st.divider()

    # --- Promo cards ---
    for p in filtered:
        rank        = p["rank"]
        score       = p.get("final_score", 0) or 0
        dur         = p.get("total_duration_sec", 0)
        eps         = p.get("episodes", [])
        ep_label    = f"Ep {eps[0]}" if len(eps) == 1 else f"Eps {', '.join(str(e) for e in eps)}"
        seg         = p["segments"][0]
        heading     = seg.get("scene_heading", "—")
        start_ts    = seg.get("start_ts", "—")
        end_ts      = seg.get("end_ts", "—")
        sc_num      = seg.get("scene_number", "—")
        hook_text   = p.get("opening_hook", {}).get("text", "—")
        cliff_text  = p.get("closing_cliffhanger", {}).get("text", "—")
        context     = p.get("narrative_context", "—")
        sfx_flag    = p.get("has_cliffhanger_sfx", False)
        sfx_note    = p.get("cliffhanger_sfx_note", "")
        validation  = p.get("validation", {})
        scoring     = p.get("scoring", {})
        warnings    = validation.get("warnings", [])

        label = f"**#{rank}** · {ep_label} · Scene {sc_num} · `{start_ts}` → `{end_ts}` ({dur:.1f}s) · Score {score:.2f}"
        with st.expander(label, expanded=(rank <= 3)):
            col_l, col_r = st.columns([2, 1])

            with col_l:
                st.markdown(f"### {heading}")
                st.markdown(f"**🎣 Opening Hook** *(establishes within first 3s)*")
                st.info(hook_text)
                st.markdown(f"**🌊 Closing Cliffhanger**")
                st.warning(cliff_text)
                if sfx_flag and sfx_note:
                    st.caption(f"🔔 SFX signal (supporting only): {sfx_note}")
                st.markdown(f"**📝 Narrative Context** *(why this works as standalone promo)*")
                st.write(context)
                if warnings:
                    st.markdown("**⚠️ Validation Warnings** *(non-disqualifying)*")
                    for w in warnings:
                        st.caption(f"• {w}")

            with col_r:
                st.markdown("#### Score Breakdown")
                scores_block = scoring.get("scores", {})

                ai_scores = scores_block.get("AI-generated", {})
                prog_scores = scores_block.get("programmatic", {})

                st.markdown("**⚡ AI-Generated** *(LLM estimates)*")
                for dim, info in ai_scores.items():
                    s = info.get("score", 0)
                    w = info.get("weight", 0)
                    dim_label = dim.replace("_", " ").title()
                    bar_pct = int(s * 10)
                    st.markdown(
                        f"<small>{dim_label} ({w:.0%})</small><br>"
                        f"<span class='score-ai'>{s:.1f}/10</span> "
                        f"{'█' * (bar_pct // 10)}{'░' * (10 - bar_pct // 10)}",
                        unsafe_allow_html=True,
                    )

                st.markdown("**🔒 Programmatic** *(deterministic rules)*")
                for dim, info in prog_scores.items():
                    s = info.get("score", 0)
                    w = info.get("weight", 0)
                    dim_label = dim.replace("_", " ").title()
                    st.markdown(
                        f"<small>{dim_label} ({w:.0%})</small> "
                        f"<span class='score-prog'>{s:.1f}/10</span>",
                        unsafe_allow_html=True,
                    )

                st.markdown(f"**Final Score: `{score:.3f}`**")
                st.progress(min(score / 10, 1.0))

                st.markdown("#### 🔒 Validation")
                if validation.get("passed"):
                    st.success("✓ All checks passed")
                else:
                    for fail in validation.get("failures", []):
                        st.error(f"✗ {fail}")

                # Segment details
                st.markdown("#### 📌 Segments")
                for i, seg_i in enumerate(p["segments"], 1):
                    st.markdown(
                        f"`Ep{seg_i['episode_number']} Sc{seg_i['scene_number']}` "
                        f"`{seg_i['start_ts']}` → `{seg_i['end_ts']}` "
                        f"({seg_i['duration_sec']:.1f}s)",
                        unsafe_allow_html=True,
                    )
                st.caption("⚠️ Timestamps are **scene-relative** (reset per scene).")


# =============================================================================
# TAB 2 — Quality Report
# =============================================================================
with tab2:
    st.title("📋 Quality Report")
    quality = load_quality()
    if not quality:
        st.error("Quality report not found. Run the pipeline first.")
        st.stop()

    counts = quality.get("candidate_counts", {})
    val_sum = quality.get("validation_summary", {})

    # Headline metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Generated", counts.get("total_generated", quality.get("total_candidates", 0)))
    c2.metric("Passed Validation", counts.get("passed_validation", quality.get("valid_candidates", 0)))
    c3.metric("Failed Validation", counts.get("failed_validation", quality.get("invalid_candidates", 0)))
    c4.metric("Duplicate Pairs Found", val_sum.get("duplicate_pairs_found", quality.get("duplicates_found", 0)))

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("Validation Breakdown")
        st.markdown(f"**Timestamp Errors:** {val_sum.get('timestamp_errors', 0)}")
        st.markdown(f"**Hallucination Errors:** {val_sum.get('hallucination_errors', 0)}")
        st.markdown(f"**Duration Violations:** {val_sum.get('duration_errors', 0)}")
        
        st.markdown("---")
        st.subheader("Failure Type Distribution")
        ft = val_sum.get("failure_type_counts") or quality.get("failure_type_counts", {})
        if ft:
            max_val = max(ft.values()) if ft.values() else 1
            for ftype, count in sorted(ft.items(), key=lambda x: -x[1]):
                st.markdown(f"**{ftype}**: {count}")
                st.progress(min(count / max_val, 1.0))
        else:
            st.success("No validation failures!")

    with col_b:
        st.subheader("Score Distribution & Coverage")
        dist = quality.get("score_distribution", {})
        cov = quality.get("coverage", {})
        st.markdown(f"**Top Score:** `{dist.get('top', '—')}`")
        st.markdown(f"**Average Score:** `{dist.get('average', '—')}`")
        st.markdown(f"**Minimum Valid Score:** `{dist.get('minimum', '—')}`")
        st.markdown(f"**Episodes with Candidates:** `{len(cov.get('episodes_with_at_least_one_candidate', []))}/50`")

        missing_eps = cov.get("episodes_with_no_candidates", [])
        if missing_eps:
            st.warning(f"Episodes without candidates: {missing_eps}")
        else:
            st.success("✓ All 50 episodes have generated candidates!")

    st.divider()
    st.subheader("Full Quality Report (raw JSON)")
    with st.expander("View JSON"):
        st.json(quality)


# =============================================================================
# TAB 3 — Failure Analysis
# =============================================================================
with tab3:
    st.title("⚠️ Failure Analysis")
    st.caption(
        "This section documents known limitations of the system — both individual candidate "
        "failures and structural weaknesses of the AI + rule-based approach."
    )

    failure = load_failure()
    if not failure:
        st.error("Failure analysis file not found. Run the pipeline first.")
        st.stop()

    # Summary
    summary = failure.get("summary", {})
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Generated", summary.get("total_generated", summary.get("total_candidates", 0)))
    c2.metric("Validation Failures", summary.get("failed_validation", summary.get("validation_failure_count", 0)))
    c3.metric("Weak Candidates", summary.get("weak_valid_candidates", summary.get("weak_candidate_count", 0)))

    st.divider()

    # System limitations
    st.subheader("🔬 Documented System Limitations")
    limitations = failure.get("known_system_limitations") or failure.get("system_limitations", [])
    for lim in limitations:
        cat = lim.get("category") or lim.get("limitation", "?")
        with st.expander(f"**{cat}**"):
            st.markdown(f"**Description:** {lim.get('description','')}")
            if "impact" in lim:
                st.markdown(f"**Impact:** {lim.get('impact','')}")
            st.markdown(f"**Mitigation:** {lim.get('mitigation','')}")

    st.divider()

    # Validation failures
    st.subheader("🚫 Validation Failure Details")
    val_failures = failure.get("validation_failures", [])
    if val_failures:
        for vf in val_failures[:20]:
            with st.expander(f"{vf.get('candidate_id','?')} — {vf.get('failure_type','?')}"):
                st.markdown(f"**Episode(s):** {vf.get('episodes', '?')}")
                st.markdown(f"**Duration:** {vf.get('duration_sec', '?')}s")
                st.error(vf.get("reason", "?"))
    else:
        st.success("No validation failures recorded.")

    st.divider()

    # Weak candidates
    st.subheader("📉 Weak Candidates Sample")
    weak = failure.get("weak_candidates", [])
    if weak:
        for w in weak[:10]:
            st.markdown(
                f"• `{w.get('candidate_id','?')}` — "
                f"Ep{w.get('episodes','?')} — "
                f"Score: {w.get('final_score','?')} — "
                f"Duration: {w.get('duration_sec','?')}s"
            )
    else:
        st.success("No weak candidates below threshold.")

    st.divider()
    st.subheader("Full Failure Analysis (raw JSON)")
    with st.expander("View JSON"):
        st.json(failure)


# =============================================================================
# TAB 4 — Source Viewer
# =============================================================================
with tab4:
    st.title("📖 Source Screenplay Viewer")
    st.caption(
        "Trace any promo recommendation back to its original screenplay. "
        "Every timestamp in the output refers to scene-relative time — "
        "each scene resets to 00:00.00."
    )

    data = load_promos()
    promos = data.get("ranked_promos", []) if data else []

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        # Allow selecting from ranked promos or manual episode entry
        mode = st.radio("Mode", ["Select from ranked promos", "Browse episode directly"], horizontal=True)

    if mode == "Select from ranked promos" and promos:
        with col_sel2:
            promo_labels = [
                f"#{p['rank']} · Ep{p['episodes']} · {p['segments'][0].get('start_ts','?')}–{p['segments'][0].get('end_ts','?')}"
                for p in promos
            ]
            selected_idx = st.selectbox("Select promo", range(len(promo_labels)), format_func=lambda i: promo_labels[i])

        selected = promos[selected_idx]
        ep_num = selected["segments"][0]["episode_number"]
        sc_num = selected["segments"][0]["scene_number"]
        start_ts = selected["segments"][0]["start_ts"]
        end_ts   = selected["segments"][0]["end_ts"]

        st.markdown(f"#### Promo #{selected['rank']} — Ep{ep_num} Sc{sc_num} · `{start_ts}` → `{end_ts}`")
        st.info(f"**Hook:** {selected.get('opening_hook',{}).get('text','—')}")
        st.warning(f"**Cliffhanger:** {selected.get('closing_cliffhanger',{}).get('text','—')}")
        st.markdown("---")

    else:
        with col_sel2:
            ep_num = st.number_input("Episode Number", 1, 50, 1)

    # Load and display the script
    script_text = load_episode_text(ep_num)
    st.markdown(f"#### Episode {ep_num} — Raw Screenplay")
    st.text_area(
        "Screenplay",
        value=script_text,
        height=600,
        help="Raw screenplay text. Scene timestamps are scene-relative (reset to 00:00.00 per scene).",
    )
    st.caption(
        "⚠️ **Timestamp note:** All timestamps shown in promo recommendations are scene-relative. "
        "Each scene heading resets the timer to 00:00.00. Never treat timestamps from different scenes "
        "as a continuous timeline."
    )


# =============================================================================
# TAB 5 — Run Pipeline
# =============================================================================
with tab5:
    st.title("⚙️ Run Pipeline")
    st.caption(
        "Trigger a fresh analysis run. For the **mock** provider no API key is needed. "
        "For **gemini** or **openai**, set the corresponding key in your `.env` file first."
    )

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        provider = st.selectbox("LLM Provider", ["mock", "gemini", "openai"], index=0)
    with col_c2:
        model_map = {
            "mock": "gemini-1.5-flash",
            "gemini": "gemini-1.5-flash",
            "openai": "gpt-4o-mini",
        }
        model = st.text_input("Model", value=model_map.get(provider, "gemini-1.5-flash"))
    with col_c3:
        top_n = st.number_input("Top N promos to rank", 1, 50, 20)

    ep_filter_ui = st.text_input(
        "Episodes (comma-separated, blank = all 50)",
        placeholder="e.g. 1,2,3,10"
    )
    verbose = st.checkbox("Verbose logging")

    if provider != "mock":
        st.warning(
            f"⚠️ You selected `{provider}`. Ensure the corresponding API key is set in your `.env` file. "
            "No charges will be incurred without your approval."
        )

    run_btn = st.button("🚀 Run Pipeline", type="primary", use_container_width=True)

    if run_btn:
        cmd = [
            sys.executable, str(ROOT / "src" / "pipeline.py"),
            "--provider", provider,
            "--model", model,
            "--top-n", str(top_n),
        ]
        if ep_filter_ui.strip():
            cmd += ["--episodes"] + [e.strip() for e in ep_filter_ui.split(",") if e.strip()]
        if verbose:
            cmd.append("--verbose")

        st.markdown("**Running pipeline...**")
        log_placeholder = st.empty()
        progress_bar = st.progress(0)

        with st.spinner("Analysing screenplay..."):
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(ROOT),
                )
                log_lines = []
                ep_count = 0
                for line in proc.stdout:
                    line = line.rstrip()
                    log_lines.append(line)
                    if "STEP" in line or "Wrote" in line or "PIPELINE" in line or "ERROR" in line:
                        log_placeholder.text("\n".join(log_lines[-20:]))
                    if "total so far:" in line:
                        try:
                            ep_count = int(line.split("total so far:")[1].split(")")[0].strip())
                            progress_bar.progress(min(ep_count / 220, 1.0))
                        except Exception:
                            pass

                proc.wait()
                if proc.returncode == 0:
                    st.success("✅ Pipeline completed successfully!")
                    clear_cache()
                    st.rerun()
                else:
                    st.error("❌ Pipeline failed. See log below.")
                log_placeholder.text("\n".join(log_lines[-40:]))

            except Exception as e:
                st.error(f"Failed to start pipeline: {e}")

    st.divider()
    st.subheader("📋 Pipeline Configuration")
    config_path = ROOT / "config" / "config.yaml"
    if config_path.exists():
        st.code(config_path.read_text(encoding="utf-8"), language="yaml")
    else:
        st.warning("config/config.yaml not found.")

    st.subheader("🔑 Environment Variables")
    env_example = ROOT / ".env.example"
    if env_example.exists():
        st.code(env_example.read_text(encoding="utf-8"), language="bash")
    else:
        st.code(
            "# Create a .env file in the project root with:\n"
            "GEMINI_API_KEY=your_gemini_api_key_here\n"
            "# OPENAI_API_KEY=your_openai_api_key_here",
            language="bash",
        )

    st.markdown(
        "> **Security:** API keys are loaded from `.env` at runtime. "
        "Never commit `.env` to version control. The `.gitignore` excludes it by default."
    )

