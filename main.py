#!/usr/bin/env python3
"""CLI entrypoint for the Ukraine-US Leads discovery/qualification system.

Usage:
    python main.py                              # autonomous discovery, dry-run per config.yaml
    python main.py --seed config/seed_sources.csv
    python main.py --live                       # override config: run against real providers
    python main.py --max-records 100             # cap for a small validation run
    python main.py --reset                       # clear checkpoints and re-run from scratch
    python main.py --stage seed --live           # run ONLY Stage 1 (seed source ingestion +
                                                  # extraction), skipping every later stage
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from pathlib import Path

from src.config import AppConfig
from src.logging_setup import configure_logging, get_logger
from src.orchestrator import Orchestrator

log = get_logger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ukraine-US Leads discovery system")
    parser.add_argument("--seed", default="config/seed_sources.csv", help="Path to seed sources CSV")
    parser.add_argument("--live", action="store_true", help="Disable dry-run (make real provider calls)")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run even if .env says otherwise")
    parser.add_argument("--max-records", type=int, default=None, help="Cap total discovered records (small test runs)")
    parser.add_argument("--reset", action="store_true", help="Clear checkpoints before running")
    parser.add_argument(
        "--stage",
        choices=["full", "seed"],
        default="full",
        help="'seed' runs ONLY Stage 1 (seed source ingestion + extraction); 'full' runs the whole pipeline",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.live:
        os.environ["DRY_RUN"] = "false"
    if args.dry_run:
        os.environ["DRY_RUN"] = "true"

    config = AppConfig.load()
    configure_logging(level=config.log_level, json_output=config.get("logging.json", True))

    if args.max_records is not None:
        config.raw.setdefault("run", {})["max_records"] = args.max_records

    if args.reset:
        from src.checkpoint import CheckpointStore

        CheckpointStore(config.checkpoint_dir).clear()
        log.info("checkpoints_cleared")

    seed_path = args.seed if args.seed and Path(args.seed).exists() else None
    if args.seed and seed_path is None:
        log.warning("seed_file_not_found", path=args.seed)

    orchestrator = Orchestrator(config)

    if args.stage == "seed":
        if not seed_path:
            log.error("seed_stage_requires_seed_file", path=args.seed)
            print(f"\nERROR: --stage seed requires a seed file; {args.seed} not found.\n")
            return 1
        state = asyncio.run(orchestrator.run_seed_discovery_only(seed_path))
        print(
            f"\nSeed discovery (Stage 1) done. sources={len(state.sources)} "
            f"companies={len(state.companies)} people={len(state.people)}\n"
            f"Output written to: {config.output_dir} (sources.csv, companies.csv, people.csv)\n"
        )
        return 0

    state = asyncio.run(orchestrator.run(seed_path))

    log.info(
        "run_complete",
        sources=len(state.sources),
        companies=len(state.companies),
        people=len(state.people),
        qualified_accounts=len(state.qualified_rows),
        manual_review=len(state.manual_review),
        dry_run=config.dry_run,
    )
    print(
        f"\nDone. sources={len(state.sources)} companies={len(state.companies)} "
        f"people={len(state.people)} qualified_accounts={len(state.qualified_rows)} "
        f"manual_review={len(state.manual_review)}\nOutput written to: {config.output_dir}\n"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
