# =============================================================================
# pipeline.py — Full End-to-End Pipeline Runner
#
# Usage:
#   python src/pipeline.py                        # uses config.yaml defaults
#   python src/pipeline.py --provider mock        # override LLM provider
#   python src/pipeline.py --provider gemini      # use real Gemini API
#   python src/pipeline.py --episodes 1 5 10      # only specific episodes
#
# Output: outputs/promos.json, promos.csv, failure_analysis.json, quality_report.json
#
# Reproducibility: Run again on new screenplay inputs by changing
#   config.yaml → paths.scripts_dir
# No source code changes required.
# =============================================================================

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Setup path so modules import correctly from any working directory
# ---------------------------------------------------------------------------
SRC_DIR    = Path(__file__).parent
ROOT_DIR   = SRC_DIR.parent
CONFIG_DIR = ROOT_DIR / "config"
OUT_DIR    = ROOT_DIR / "outputs"

sys.path.insert(0, str(SRC_DIR))

from parser    import load_all_episodes
from validator import validate_all, ValidationConfig
from analyzer  import PromoAnalyzer
from scorer    import score_and_rank, DEFAULT_WEIGHTS
from reporter  import (
    write_promos_json, write_promos_csv,
    write_failure_analysis, write_quality_report,
)
from llm_client import create_llm_client, ResponseCache

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    """Load config.yaml. Returns defaults if file not found."""
    try:
        import yaml
        with config_path.open('r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except ImportError:
        logging.warning("PyYAML not installed — using built-in defaults")
    except FileNotFoundError:
        logging.warning(f"Config not found at {config_path} — using defaults")

    # Fallback defaults (matches config.yaml)
    return {
        "paths": {
            "scripts_dir": "data/scripts/I Married a Broken Soldier. He was a Duke",
            "output_dir":  "outputs",
            "cache_dir":   "outputs/cache",
        },
        "llm": {
            "provider":      "mock",
            "model":         "gemini-1.5-flash",
            "request_delay": 4,
            "max_retries":   3,
            "temperature":   0.2,
        },
        "scoring": {
            "weights": {
                "hook_strength":        0.25,
                "cliffhanger_strength": 0.30,
                "standalone_clarity":   0.20,
                "emotional_impact":     0.15,
                "duration_quality":     0.10,
            },
            "ideal_min_seconds": 25,
            "ideal_max_seconds": 45,
            "hard_min_seconds":  20,
            "hard_max_seconds":  60,
        },
        "output": {
            "top_n": 20,
        }
    }


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Data quality notes (from pre-analysis)
# ---------------------------------------------------------------------------

DATA_QUALITY_NOTES = [
    {
        "episode": 6,
        "type": "FORMAT_VARIANT",
        "description": "Uses ALL-CAPS field labels (SCENE HEADING, SCENE START, SCENE END). "
                       "Parser auto-detects and handles correctly.",
        "impact": "None — parsed successfully with zero warnings.",
    },
    {
        "episode": 22,
        "scene": 1,
        "type": "BOUNDARY_OVERHANG",
        "description": "SOUND FX event ends at 00:42.80 while Scene end is 00:42.50 (0.30s overhang in source).",
        "impact": "Minor — preserved verbatim. Validator uses ±0.5s tolerance.",
    },
]


# ---------------------------------------------------------------------------
# Main pipeline
# ---------------------------------------------------------------------------

def run_pipeline(
    config: dict,
    provider_override: Optional[str] = None,
    model_override: Optional[str] = None,
    episode_filter: Optional[list[int]] = None,
    verbose: bool = False,
) -> dict:
    """
    Execute the complete promo discovery pipeline.
    Returns a summary dict suitable for display or logging.
    """
    setup_logging(verbose)
    logger = logging.getLogger(__name__)

    start_time = time.time()

    # --- Resolve paths ---
    scripts_dir = ROOT_DIR / config["paths"]["scripts_dir"]
    output_dir  = ROOT_DIR / config["paths"]["output_dir"]
    cache_dir   = ROOT_DIR / config["paths"]["cache_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # --- Scoring config ---
    scoring_cfg   = config.get("scoring", {})
    weights       = scoring_cfg.get("weights", DEFAULT_WEIGHTS)
    ideal_min     = float(scoring_cfg.get("ideal_min_seconds", 25))
    ideal_max     = float(scoring_cfg.get("ideal_max_seconds", 45))
    hard_min      = float(scoring_cfg.get("hard_min_seconds", 20))
    hard_max      = float(scoring_cfg.get("hard_max_seconds", 60))
    top_n         = int(config.get("output", {}).get("top_n", 20))

    val_config = ValidationConfig(
        hard_min_seconds=hard_min,
        hard_max_seconds=hard_max,
        ideal_min_seconds=ideal_min,
        ideal_max_seconds=ideal_max,
    )

    # --- LLM setup ---
    llm_cfg = config.get("llm", {}).copy()
    if provider_override:
        llm_cfg["provider"] = provider_override
    if model_override:
        llm_cfg["model"] = model_override

    # Load .env if present
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv(env_path)
            logger.info(f"Loaded .env from {env_path}")
        except ImportError:
            # Manual parse
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    import os
                    os.environ.setdefault(k.strip(), v.strip())

    logger.info(f"LLM provider: {llm_cfg['provider']} / model: {llm_cfg.get('model','?')}")

    try:
        llm_client = create_llm_client(llm_cfg, cache_dir=cache_dir)
    except ValueError as e:
        logger.error(f"LLM setup failed: {e}")
        logger.info("Falling back to mock provider")
        llm_cfg["provider"] = "mock"
        llm_client = create_llm_client(llm_cfg, cache_dir=cache_dir)

    # =========================================================================
    # STEP 1: Parse all episodes
    # =========================================================================
    logger.info(f"{'='*60}")
    logger.info(f"STEP 1: Parsing episodes from {scripts_dir}")
    logger.info(f"{'='*60}")

    if not scripts_dir.exists():
        raise FileNotFoundError(f"Scripts directory not found: {scripts_dir}")

    episodes, parse_report = load_all_episodes(scripts_dir)

    if episode_filter:
        episodes = [e for e in episodes if e.episode_number in episode_filter]
        logger.info(f"Filtered to episodes: {[e.episode_number for e in episodes]}")

    logger.info(f"Parsed {len(episodes)} episodes "
                f"(warnings: {parse_report['parsed_with_warnings']}, "
                f"errors: {len(parse_report['parse_errors'])})")

    if parse_report['parse_errors']:
        for err in parse_report['parse_errors']:
            logger.error(f"  Parse error: {err}")

    ep_map = {e.episode_number: e for e in episodes}

    # =========================================================================
    # STEP 2: Generate promo candidates
    # =========================================================================
    logger.info(f"{'='*60}")
    logger.info(f"STEP 2: Generating promo candidates (LLM: {llm_cfg['provider']})")
    logger.info(f"{'='*60}")

    analyzer = PromoAnalyzer(llm_client=llm_client, cfg={"hard_min_seconds": hard_min, "hard_max_seconds": hard_max})

    total_eps = len(episodes)
    all_candidates = []

    for i, episode in enumerate(episodes, 1):
        ep_candidates = analyzer.analyze_episode(episode)
        all_candidates.extend(ep_candidates)
        logger.info(
            f"  [{i:>3}/{total_eps}] Ep{episode.episode_number:>3}: "
            f"{len(ep_candidates):>2} candidates  "
            f"(total so far: {len(all_candidates)})"
        )

    logger.info(f"Generated {len(all_candidates)} total candidates")

    # =========================================================================
    # STEP 3: Validate candidates
    # =========================================================================
    logger.info(f"{'='*60}")
    logger.info(f"STEP 3: Validating candidates")
    logger.info(f"{'='*60}")

    all_candidates, validation_report = validate_all(all_candidates, ep_map, val_config)

    valid_count   = validation_report["valid_candidates"]
    invalid_count = validation_report["invalid_candidates"]
    logger.info(f"Valid: {valid_count}  |  Invalid: {invalid_count}  |  Duplicates: {validation_report['duplicates_found']}")

    if validation_report["failure_type_counts"]:
        logger.info("Failure type breakdown:")
        for ftype, count in validation_report["failure_type_counts"].items():
            logger.info(f"  {ftype}: {count}")

    # =========================================================================
    # STEP 4: Score and rank
    # =========================================================================
    logger.info(f"{'='*60}")
    logger.info(f"STEP 4: Scoring and ranking (top {top_n})")
    logger.info(f"{'='*60}")

    ranked_candidates, score_breakdowns = score_and_rank(
        all_candidates,
        weights=weights,
        ideal_min=ideal_min,
        ideal_max=ideal_max,
        hard_min=hard_min,
        hard_max=hard_max,
        top_n=top_n,
    )

    if ranked_candidates:
        logger.info(f"Top 5 promos:")
        for c in ranked_candidates[:5]:
            seg = c.segments[0]
            logger.info(
                f"  #{c.rank} Ep{seg.episode_number} Sc{seg.scene_number} "
                f"{seg.start_ts}–{seg.end_ts} ({c.total_duration_sec:.1f}s) "
                f"score={c.final_score:.4f}"
            )

    # =========================================================================
    # STEP 5: Write outputs
    # =========================================================================
    logger.info(f"{'='*60}")
    logger.info(f"STEP 5: Writing outputs to {output_dir}")
    logger.info(f"{'='*60}")

    elapsed = round(time.time() - start_time, 1)
    pipeline_metadata = {
        "show":               "I Married a Broken Soldier. He was a Duke",
        "episodes_processed": len(episodes),
        "llm_provider":       llm_cfg["provider"],
        "llm_model":          llm_cfg.get("model", "?"),
        "scoring_weights":    weights,
        "hard_min_seconds":   hard_min,
        "hard_max_seconds":   hard_max,
        "ideal_range":        f"{ideal_min}–{ideal_max}s",
        "pipeline_duration_sec": elapsed,
        "cache_hits":         sum(1 for c in cache_dir.glob("*.json")),
    }

    write_promos_json(
        ranked_candidates, all_candidates, score_breakdowns,
        output_dir / "promos.json", pipeline_metadata
    )
    write_promos_csv(
        ranked_candidates, score_breakdowns,
        output_dir / "promos.csv"
    )
    write_failure_analysis(
        all_candidates, validation_report, score_breakdowns,
        output_dir / "failure_analysis.json",
        DATA_QUALITY_NOTES
    )
    write_quality_report(
        all_candidates, ranked_candidates, validation_report,
        score_breakdowns, output_dir / "quality_report.json",
        pipeline_metadata
    )

    # =========================================================================
    # Summary
    # =========================================================================
    summary = {
        "episodes_processed":   len(episodes),
        "total_candidates":     len(all_candidates),
        "valid_candidates":     valid_count,
        "invalid_candidates":   invalid_count,
        "ranked_output":        len(ranked_candidates),
        "top_score":            ranked_candidates[0].final_score if ranked_candidates else 0,
        "pipeline_duration_sec": elapsed,
        "output_dir":           str(output_dir),
    }

    logger.info(f"{'='*60}")
    logger.info(f"PIPELINE COMPLETE in {elapsed}s")
    logger.info(f"  Candidates: {len(all_candidates)} generated → {valid_count} valid → {len(ranked_candidates)} ranked")
    logger.info(f"  Outputs:    {output_dir}")
    logger.info(f"{'='*60}")

    return summary


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Kuku FM Promo Discovery System — Full Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python src/pipeline.py                     # run with config.yaml defaults
          python src/pipeline.py --provider mock     # no API key needed (testing)
          python src/pipeline.py --provider groq     # Groq API (needs GROQ_API_KEY in .env)
          python src/pipeline.py --provider gemini   # real Gemini API (needs GEMINI_API_KEY in .env)
          python src/pipeline.py --top-n 10          # keep top 10 promos
          python src/pipeline.py --episodes 1 10 36  # specific episodes only
          python src/pipeline.py --verbose            # detailed logging
        """),
    )
    parser.add_argument("--provider", choices=["gemini", "openai", "groq", "mock"],
                        help="Override LLM provider from config.yaml")
    parser.add_argument("--model", help="Override LLM model name")
    parser.add_argument("--top-n", type=int, default=None,
                        help="Number of top promos to include in output")
    parser.add_argument("--episodes", nargs="+", type=int, default=None,
                        help="Only process specific episode numbers")
    parser.add_argument("--config", default=None,
                        help="Path to config.yaml (default: config/config.yaml)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Verbose debug logging")
    args = parser.parse_args()

    config_path = Path(args.config) if args.config else CONFIG_DIR / "config.yaml"
    config = load_config(config_path)

    if args.top_n:
        config.setdefault("output", {})["top_n"] = args.top_n

    try:
        summary = run_pipeline(
            config=config,
            provider_override=args.provider,
            model_override=args.model,
            episode_filter=args.episodes,
            verbose=args.verbose,
        )
        print(f"\n✓ Pipeline complete — {summary['ranked_output']} promos ranked in {summary['pipeline_duration_sec']}s")
        print(f"  Outputs: {summary['output_dir']}")
    except Exception as e:
        logging.getLogger(__name__).error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


import textwrap
if __name__ == "__main__":
    main()

