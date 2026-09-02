#!/usr/bin/env python3
"""
Fetch the four core SEO scale metrics for a list of domains from
DataForSEO Labs / Backlinks:

  pages     -- count of pages that rank for at least one keyword
               (dataforseo_labs/google/relevant_pages). This is a proxy for
               "pages in the index that actually do SEO work", which is
               more useful for a competitive comparison than a raw crawled
               page count or a `site:` search estimate (Google no longer
               gives a trustworthy number for the latter — don't bother
               trying to use `site:domain` result counts for this).
  referring_domains -- from backlinks/summary. The standard link-profile
               breadth metric ("домены-доноры").
  keywords  -- organic.count from dataforseo_labs/google/domain_rank_overview.
  traffic   -- organic.etv from the same call: DataForSEO's estimated
               monthly organic traffic (visits), NOT a dollar figure — the
               dollar-equivalent is the separate estimated_paid_traffic_cost
               field, which this script does not collect.

Usage:
    python3 domain_metrics.py --domains domains.txt --location "Ukraine" \
        --language ru --out metrics.json
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
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    domains = [d.strip() for d in Path(args.domains).read_text(encoding="utf-8").splitlines() if d.strip() and not d.startswith("#")]

    metrics = []
    for dom in domains:
        print(f"  fetching metrics: {dom} ...", file=sys.stderr)

        dro = post("dataforseo_labs/google/domain_rank_overview/live",
                    [{"target": dom, "location_name": args.location, "language_code": args.language}], retries=1)
        dro_result = first_result(dro)
        keywords = traffic = None
        if dro_result and dro_result.get("items"):
            organic = dro_result["items"][0]["metrics"]["organic"]
            keywords = organic.get("count")
            traffic = round(organic["etv"]) if organic.get("etv") is not None else None

        bl = post("backlinks/summary/live",
                   [{"target": dom, "internal_list_limit": 10}], retries=1)
        bl_result = first_result(bl)
        referring_domains = bl_result.get("referring_domains") if bl_result else None

        rp = post("dataforseo_labs/google/relevant_pages/live",
                   [{"target": dom, "location_name": args.location, "language_code": args.language, "limit": 1}], retries=1)
        rp_result = first_result(rp)
        pages = rp_result.get("total_count") if rp_result else None

        metrics.append({
            "domain": dom,
            "pages": pages,
            "referring_domains": referring_domains,
            "keywords": keywords,
            "traffic": traffic,
        })

    Path(args.out).write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved metrics for {len(domains)} domains -> {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
