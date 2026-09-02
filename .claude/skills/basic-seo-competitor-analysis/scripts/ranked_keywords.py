#!/usr/bin/env python3
"""
Fetch each domain's top ranked keywords (by search volume) from DataForSEO
Labs. This is not a metric by itself — it's the raw material for judging
what a competitor actually sells, which a pure domain name or a couple of
SERP snippets can't reliably tell you.

Read the returned keyword lists yourself and classify each domain (e.g.
"only engines" vs "all auto parts" vs "wrong niche entirely") by what
those keywords are actually about — not by the domain's name. A store
called "engineparts.com.ua" that ranks only for engine model codes really
is an engine specialist; a store called "euromotors.com.ua" that ranks for
gearboxes, AC compressors and sensors is not, whatever its name suggests.
A domain whose top keywords are unrelated to the product category entirely
(e.g. motorcycle helmets when you're analyzing car-engine sellers, or
random unrelated retail goods) is probably not a real competitor and
should be flagged for exclusion rather than forced into a category.

Usage:
    python3 ranked_keywords.py --domains domains.txt --location "Ukraine" \
        --language ru --limit 50 --out ranked_keywords.json

domains.txt: one domain per line, e.g.:
    motopoland.com.ua
    engineparts.com.ua
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dfs_common import post, first_result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", required=True, help="text file, one domain per line")
    ap.add_argument("--location", default="Ukraine")
    ap.add_argument("--language", default="ru")
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    domains = [d.strip() for d in Path(args.domains).read_text(encoding="utf-8").splitlines() if d.strip() and not d.startswith("#")]

    out = {}
    for dom in domains:
        payload = [{
            "target": dom,
            "location_name": args.location,
            "language_code": args.language,
            "limit": args.limit,
            "order_by": ["keyword_data.keyword_info.search_volume,desc"],
            "load_html": False,
        }]
        print(f"  fetching ranked keywords: {dom} ...", file=sys.stderr)
        data = post("dataforseo_labs/google/ranked_keywords/live", payload, retries=1)
        result = first_result(data)
        if not result:
            out[dom] = {"total_count": None, "keywords": [], "error": "no result — check task status"}
            continue
        items = result.get("items") or []
        keywords = [it["keyword_data"]["keyword"] for it in items if it.get("keyword_data")]
        out[dom] = {
            "total_count": result.get("total_count"),
            "keywords": keywords,
        }

    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved ranked-keyword samples for {len(domains)} domains -> {args.out}", file=sys.stderr)
    print("Now READ the keyword lists yourself and classify each domain — don't skip this.", file=sys.stderr)


if __name__ == "__main__":
    main()
