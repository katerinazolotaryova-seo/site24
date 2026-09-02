#!/usr/bin/env python3
"""
Fetch the top organic Google SERP for a list of queries via DataForSEO.

Usage:
    python3 serp_top10.py --input queries.txt --location "Ukraine" --out serp_results.json

Input file: one query per line, optionally with a language suffix:
    купить мотор BMW|ru
    купити двигун Mercedes|uk
    generic query with no suffix          (uses --default-lang)

Output JSON: a flat list of rows, one per organic result actually returned
(ads, PAA, maps packs etc. are already filtered out), each with:
    {"query": ..., "position": 1, "rank_absolute": 2, "domain": ...,
     "title": ..., "url": ...}

"position" is the rank among organic results only (1-10 for a normal top-10
ask); "rank_absolute" is Google's raw slot including non-organic blocks —
keep both, the gap between them is itself informative (lots of ads above
the fold, etc).
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dfs_common import post, first_result


def parse_input(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            q, lang = line.rsplit("|", 1)
            rows.append((q.strip(), lang.strip()))
        else:
            rows.append((line, None))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="text file with one query per line (optionally 'query|lang')")
    ap.add_argument("--location", default="Ukraine")
    ap.add_argument("--default-lang", default="ru")
    ap.add_argument("--depth", type=int, default=10, help="how many organic results to keep per query")
    ap.add_argument("--device", default="desktop")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    queries = parse_input(args.input)
    all_rows = []
    for query, lang in queries:
        lang = lang or args.default_lang
        payload = [{
            "keyword": query,
            "location_name": args.location,
            "language_code": lang,
            "device": args.device,
            "os": "windows",
            "depth": max(args.depth, 10),
        }]
        print(f"  fetching SERP: {query!r} ({lang}) ...", file=sys.stderr)
        data = post("serp/google/organic/live/advanced", payload, retries=1)
        result = first_result(data)
        if not result:
            print(f"    WARNING: no result for {query!r} — check task status_message above", file=sys.stderr)
            continue
        organic = [it for it in result.get("items", []) if it.get("type") == "organic"]
        for pos, it in enumerate(organic[:args.depth], start=1):
            all_rows.append({
                "query": query,
                "position": pos,
                "rank_absolute": it.get("rank_absolute"),
                "domain": (it.get("domain") or "").replace("www.", ""),
                "title": it.get("title"),
                "url": it.get("url"),
            })

    Path(args.out).write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(all_rows)} rows across {len(queries)} queries -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
