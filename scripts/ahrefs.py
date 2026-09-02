#!/usr/bin/env python3
"""
Обёртка над Ahrefs API v3 для presale-анализа и работы с клиентскими сайтами.

Настройка:
    cp .env.example .env
    # вписать AHREFS_API_KEY=... в .env

Использование из командной строки:
    python3 scripts/ahrefs.py check                         # проверить ключ и остаток лимитов
    python3 scripts/ahrefs.py overview example.com          # DR, трафик, ключевые слова, ссылки одним отчётом
    python3 scripts/ahrefs.py backlinks example.com --limit 20
    python3 scripts/ahrefs.py keywords example.com --limit 20
    python3 scripts/ahrefs.py top-pages example.com --limit 20
    python3 scripts/ahrefs.py refdomains example.com

Использование из кода:
    from scripts.ahrefs import Ahrefs
    client = Ahrefs()
    print(client.domain_overview("example.com"))
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.ahrefs.com/v3"
ROOT = Path(__file__).resolve().parent.parent


def _load_env(env_path: Path = ROOT / ".env") -> None:
    """Простой загрузчик .env без внешних зависимостей (python-dotenv не установлен)."""
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key and key not in os.environ:
            os.environ[key] = value


_load_env()


class AhrefsError(RuntimeError):
    pass


class Ahrefs:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("AHREFS_API_KEY")
        if not self.api_key:
            raise AhrefsError(
                "AHREFS_API_KEY не найден. Впишите его в .env (см. .env.example)."
            )
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            }
        )

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, params=params or {}, timeout=30)
        if resp.status_code >= 400:
            raise AhrefsError(
                f"Ahrefs API {resp.status_code} на {path}: {resp.text[:500]}"
            )
        return resp.json()

    # --- служебное -----------------------------------------------------

    def limits_and_usage(self) -> Any:
        """Проверка ключа + остаток API-юнитов на текущий период."""
        return self._get("/subscription-info/limits-and-usage")

    # --- Site Explorer ---------------------------------------------------

    def domain_rating(self, target: str, on: str | None = None) -> Any:
        return self._get(
            "/site-explorer/domain-rating",
            {"target": target, "date": on or date.today().isoformat()},
        )

    def metrics(self, target: str, mode: str = "domain", on: str | None = None) -> Any:
        """Общие метрики: органический трафик, ключевые слова, стоимость трафика и т.д."""
        return self._get(
            "/site-explorer/metrics",
            {
                "target": target,
                "mode": mode,
                "date": on or date.today().isoformat(),
            },
        )

    def backlinks_stats(self, target: str, mode: str = "domain", on: str | None = None) -> Any:
        return self._get(
            "/site-explorer/backlinks-stats",
            {"target": target, "mode": mode, "date": on or date.today().isoformat()},
        )

    def backlinks(self, target: str, mode: str = "domain", limit: int = 50) -> Any:
        return self._get(
            "/site-explorer/all-backlinks",
            {"target": target, "mode": mode, "limit": limit},
        )

    def organic_keywords(self, target: str, mode: str = "domain", limit: int = 50) -> Any:
        return self._get(
            "/site-explorer/organic-keywords",
            {"target": target, "mode": mode, "limit": limit},
        )

    def top_pages(self, target: str, mode: str = "domain", limit: int = 50) -> Any:
        return self._get(
            "/site-explorer/top-pages",
            {"target": target, "mode": mode, "limit": limit},
        )

    def refdomains(self, target: str, mode: str = "domain", limit: int = 50) -> Any:
        return self._get(
            "/site-explorer/refdomains",
            {"target": target, "mode": mode, "limit": limit},
        )

    # --- сводка для presale ----------------------------------------------

    def domain_overview(self, target: str) -> dict[str, Any]:
        """Быстрая сводка для presale-аудита: DR, ссылочный профиль, органика."""
        overview: dict[str, Any] = {"target": target}
        for key, fn in (
            ("domain_rating", lambda: self.domain_rating(target)),
            ("metrics", lambda: self.metrics(target)),
            ("backlinks_stats", lambda: self.backlinks_stats(target)),
        ):
            try:
                overview[key] = fn()
            except AhrefsError as e:
                overview[key] = {"error": str(e)}
        return overview


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Проверить ключ и лимиты")

    p_overview = sub.add_parser("overview", help="Сводка по домену")
    p_overview.add_argument("target")

    for name in ("backlinks", "keywords", "top-pages", "refdomains"):
        p = sub.add_parser(name)
        p.add_argument("target")
        p.add_argument("--limit", type=int, default=50)

    args = parser.parse_args()
    client = Ahrefs()

    try:
        if args.cmd == "check":
            result = client.limits_and_usage()
        elif args.cmd == "overview":
            result = client.domain_overview(args.target)
        elif args.cmd == "backlinks":
            result = client.backlinks(args.target, limit=args.limit)
        elif args.cmd == "keywords":
            result = client.organic_keywords(args.target, limit=args.limit)
        elif args.cmd == "top-pages":
            result = client.top_pages(args.target, limit=args.limit)
        elif args.cmd == "refdomains":
            result = client.refdomains(args.target, limit=args.limit)
        else:  # pragma: no cover
            parser.error("unknown command")
            return
    except AhrefsError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
