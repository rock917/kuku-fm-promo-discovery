# =============================================================================
# sync_supabase.py — Direct REST API Sync to Supabase PostgreSQL Tables
#
# Uses standard library urllib.request (zero third-party dependencies required).
# =============================================================================

from __future__ import annotations

import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Any, List

logger = logging.getLogger("sync-supabase")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

ROOT = Path(__file__).resolve().parent.parent
OUTPUTS = ROOT / "outputs"


class SupabaseRestClient:
    """Lightweight REST client for Supabase PostgREST endpoints."""

    def __init__(self, url: str, key: str):
        self.base_url = url.rstrip('/') + '/rest/v1'
        self.key = key
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
            "User-Agent": "Kuku-Promo-Sync/1.0",
        }

    def insert(self, table: str, payload: Any) -> List[dict]:
        """Insert one record or a list of records into table."""
        endpoint = f"{self.base_url}/{table}"
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(endpoint, data=data, headers=self.headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                res_body = resp.read().decode('utf-8')
                return json.loads(res_body) if res_body else []
        except urllib.error.HTTPError as e:
            err = e.read().decode('utf-8', errors='replace')
            logger.error(f"Supabase HTTP Error on {table} ({e.code}): {err}")
            raise RuntimeError(f"Supabase insert failed on {table}: {err}")


def sync_to_supabase() -> bool:
    """Sync outputs directory files to Supabase via PostgREST."""
    supabase_url = os.environ.get("SUPABASE_URL", "").strip().strip('"\'')
    supabase_key = os.environ.get("SUPABASE_KEY", "").strip().strip('"\'')

    # Automatically clean if key name was included in value (e.g. SUPABASE_URL=https://...)
    if supabase_url.upper().startswith("SUPABASE_URL="):
        supabase_url = supabase_url.split("=", 1)[1].strip().strip('"\'')
    if supabase_key.upper().startswith("SUPABASE_KEY="):
        supabase_key = supabase_key.split("=", 1)[1].strip().strip('"\'')

    if not supabase_url or not supabase_key:
        logger.warning(
            "SUPABASE_URL or SUPABASE_KEY is missing in environment/.env. "
            "Skipping Supabase synchronization."
        )
        return False

    client = SupabaseRestClient(supabase_url, supabase_key)
    logger.info(f"Targeting Supabase instance: {supabase_url[:35]}...")

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

    try:
        run_res = client.insert("pipeline_runs", run_payload)
        if not run_res:
            logger.error("Failed to insert pipeline_run into Supabase.")
            return False
        run_id = run_res[0]["id"]
        logger.info(f"Created Supabase pipeline_runs record: {run_id}")
    except Exception as e:
        logger.error(f"Error inserting pipeline_runs: {e}")
        return False

    # 2. Insert candidates and segments
    cand_count = 0
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

        try:
            cand_res = client.insert("promo_candidates", candidate_payload)
            if not cand_res:
                continue
            cand_id = cand_res[0]["id"]
            cand_count += 1

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
                client.insert("promo_segments", seg_payloads)
        except Exception as e:
            logger.error(f"Failed inserting candidate {p.get('candidate_id')}: {e}")

    logger.info(f"Successfully synced {cand_count} candidates and segments to Supabase.")

    # 3. Insert Quality Report
    qual_file = OUTPUTS / "quality_report.json"
    if qual_file.exists():
        try:
            with open(qual_file, "r", encoding="utf-8") as f:
                qual_data = json.load(f)
            client.insert("quality_reports", {
                "run_id": run_id,
                "candidate_counts": qual_data.get("candidate_counts"),
                "validation_summary": qual_data.get("validation_summary"),
                "score_distribution": qual_data.get("score_distribution"),
                "coverage": qual_data.get("coverage"),
                "raw_report": qual_data,
            })
            logger.info("Synced quality report to Supabase.")
        except Exception as e:
            logger.error(f"Error syncing quality report: {e}")

    # 4. Insert Failure Analysis
    fail_file = OUTPUTS / "failure_analysis.json"
    if fail_file.exists():
        try:
            with open(fail_file, "r", encoding="utf-8") as f:
                fail_data = json.load(f)
            client.insert("failure_analyses", {
                "run_id": run_id,
                "summary": fail_data.get("summary"),
                "system_limitations": fail_data.get("known_system_limitations") or fail_data.get("system_limitations"),
                "validation_failures": fail_data.get("validation_failures"),
                "weak_candidates": fail_data.get("weak_candidates"),
            })
            logger.info("Synced failure analysis to Supabase.")
        except Exception as e:
            logger.error(f"Error syncing failure analysis: {e}")

    return True


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
    sync_to_supabase()
