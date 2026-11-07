# =============================================================================
# sync_supabase.py — Sync Pipeline Outputs to Supabase Database
#
# Reads outputs/promos.json, quality_report.json, failure_analysis.json
# and inserts/updates them in Supabase PostgreSQL tables.
# =============================================================================

from __future__ import annotations

import os
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("sync-supabase")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"


def sync_to_supabase() -> bool:
    """Sync outputs directory files to Supabase."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.warning(
            "SUPABASE_URL or SUPABASE_KEY is missing in environment/.env. "
            "Skipping Supabase synchronization."
        )
        return False

    try:
        from supabase import create_client, Client
    except ImportError:
        logger.error("supabase package not installed. Run: pip install supabase")
        return False

    client: Client = create_client(supabase_url, supabase_key)
    logger.info(f"Connected to Supabase: {supabase_url[:30]}...")

    promos_file = OUTPUTS / "promos.json"
    if not promos_file.exists():
        logger.error("outputs/promos.json not found. Run pipeline first.")
        return False

    with open(promos_file, "r", encoding="utf-8") as f:
        promos_data = json.load(f)

    meta = promos_data.get("metadata", {})
    ranked_promos = promos_data.get("ranked_promos", [])

    # 1. Insert pipeline run record
    run_payload = {
        "show_title": meta.get("show", "I Married a Broken Soldier. He was a Duke"),
        "episodes_processed": meta.get("episodes_processed", 50),
        "llm_provider": meta.get("llm_provider", "groq"),
        "llm_model": meta.get("llm_model", "llama-3.3-70b-versatile"),
        "total_candidates_generated": meta.get("total_candidates_generated", 0),
        "valid_candidates": meta.get("valid_candidates", 0),
        "invalid_candidates": meta.get("invalid_candidates", 0),
        "ranked_output_count": len(ranked_promos),
        "pipeline_duration_sec": meta.get("pipeline_duration_sec", 0.0),
        "scoring_weights": meta.get("scoring_weights", {}),
        "metadata": meta,
    }

    run_res = client.table("pipeline_runs").insert(run_payload).execute()
    if not run_res.data:
        logger.error("Failed to insert pipeline_run into Supabase.")
        return False

    run_id = run_res.data[0]["id"]
    logger.info(f"Created Supabase pipeline_run record: {run_id}")

    # 2. Insert candidates and segments
    for p in ranked_promos:
        scores_block = p.get("scoring", {}).get("scores", {})
        ai_scores = scores_block.get("AI-generated", {})
        prog_scores = scores_block.get("programmatic", {})

        candidate_payload = {
            "run_id": run_id,
            "candidate_id": p.get("candidate_id"),
            "rank": p.get("rank"),
            "final_score": p.get("final_score"),
            "is_valid": p.get("is_valid", True),
            "primary_episode": p.get("episodes", [1])[0],
            "episodes": p.get("episodes", []),
            "total_duration_sec": p.get("total_duration_sec"),
            "opening_hook_text": p.get("opening_hook", {}).get("text"),
            "closing_cliffhanger_text": p.get("closing_cliffhanger", {}).get("text"),
            "narrative_context": p.get("narrative_context"),
            "has_cliffhanger_sfx": p.get("has_cliffhanger_sfx", False),
            "cliffhanger_sfx_note": p.get("cliffhanger_sfx_note"),
            "ai_hook_strength": ai_scores.get("hook_strength", {}).get("score"),
            "ai_cliffhanger_strength": ai_scores.get("cliffhanger_strength", {}).get("score"),
            "ai_standalone_clarity": ai_scores.get("standalone_clarity", {}).get("score"),
            "ai_emotional_impact": ai_scores.get("emotional_impact", {}).get("score"),
            "prog_duration_quality": prog_scores.get("duration_quality", {}).get("score"),
            "score_breakdown": p.get("scoring"),
            "validation_failures": p.get("validation", {}).get("failures", []),
            "validation_warnings": p.get("validation", {}).get("warnings", []),
        }

        cand_res = client.table("promo_candidates").insert(candidate_payload).execute()
        if not cand_res.data:
            continue
        cand_id = cand_res.data[0]["id"]

        # Insert segments
        segments = p.get("segments", [])
        seg_payloads = [
            {
                "candidate_ref_id": cand_id,
                "episode_number": s.get("episode_number"),
                "scene_number": s.get("scene_number"),
                "scene_heading": s.get("scene_heading"),
                "start_ts": s.get("start_ts"),
                "end_ts": s.get("end_ts"),
                "start_sec": s.get("start_sec"),
                "end_sec": s.get("end_sec"),
                "duration_sec": s.get("duration_sec"),
                "timestamp_note": s.get("timestamp_note"),
            }
            for s in segments
        ]
        if seg_payloads:
            client.table("promo_segments").insert(seg_payloads).execute()

    logger.info(f"Successfully synced {len(ranked_promos)} candidates & segments to Supabase.")

    # 3. Insert Quality Report
    qual_file = OUTPUTS / "quality_report.json"
    if qual_file.exists():
        with open(qual_file, "r", encoding="utf-8") as f:
            qual_data = json.load(f)
        client.table("quality_reports").insert({
            "run_id": run_id,
            "candidate_counts": qual_data.get("candidate_counts"),
            "validation_summary": qual_data.get("validation_summary"),
            "score_distribution": qual_data.get("score_distribution"),
            "coverage": qual_data.get("coverage"),
            "raw_report": qual_data,
        }).execute()
        logger.info("Synced quality report to Supabase.")

    # 4. Insert Failure Analysis
    fail_file = OUTPUTS / "failure_analysis.json"
    if fail_file.exists():
        with open(fail_file, "r", encoding="utf-8") as f:
            fail_data = json.load(f)
        client.table("failure_analyses").insert({
            "run_id": run_id,
            "summary": fail_data.get("summary"),
            "system_limitations": fail_data.get("known_system_limitations") or fail_data.get("system_limitations"),
            "validation_failures": fail_data.get("validation_failures"),
            "weak_candidates": fail_data.get("weak_candidates"),
        }).execute()
        logger.info("Synced failure analysis to Supabase.")

    return True


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    sync_to_supabase()
