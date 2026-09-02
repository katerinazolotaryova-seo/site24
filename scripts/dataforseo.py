#!/usr/bin/env python3
"""
Обёртка над DataForSEO API v3 для presale-анализа и работы с клиентскими сайтами.

Аутентификация у DataForSEO — HTTP Basic Auth (логин = email аккаунта,
пароль = API-пароль из личного кабинета dataforseo.com, это НЕ тот же
пароль, что для входа на сайт).

Настройка:
    cp .env.example .env
    # вписать DATAFORSEO_LOGIN и DATAFORSEO_PASSWORD в .env

Использование из командной строки:
    python3 scripts/dataforseo.py check                       # баланс (бесплатно)
    python3 scripts/dataforseo.py serp "seo аудит сайта" --location "Ukraine" --language ru
    python3 scripts/dataforseo.py ranked-keywords example.com --limit 20
    python3 scripts/dataforseo.py backlinks-summary example.com

Использование из кода:
    from scripts.dataforseo import DataForSEO
    client = DataForSEO()
    print(client.user_data())
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.dataforseo.com/v3"
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


class DataForSEOError(RuntimeError):
    pass


class DataForSEO:
    def __init__(self, login: str | None = None, password: str | None = None):
        self.login = login or os.environ.get("DATAFORSEO_LOGIN")
        self.password = password or os.environ.get("DATAFORSEO_PASSWORD")
        if not self.login or not self.password:
            raise DataForSEOError(
                "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD не найдены. "
                "Впишите их в .env (см. .env.example)."
            )
        self.session = requests.Session()
        self.session.auth = (self.login, self.password)

    def _post(self, path: str, payload: list[dict[str, Any]]) -> Any:
        url = f"{BASE_URL}{path}"
        resp = self.session.post(url, json=payload, timeout=60)
        if resp.status_code >= 400:
            raise DataForSEOError(f"DataForSEO API {resp.status_code} на {path}: {resp.text[:500]}")
        data = resp.json()
        if data.get("status_code") != 20000:
            raise DataForSEOError(f"DataForSEO API вернул ошибку: {data.get('status_message')}")
        return data

    def _get(self, path: str) -> Any:
        url = f"{BASE_URL}{path}"
        resp = self.session.get(url, timeout=30)
        if resp.status_code >= 400:
            raise DataForSEOError(f"DataForSEO API {resp.status_code} на {path}: {resp.text[:500]}")
        return resp.json()

    # --- служебное ---------------------------------------------------------

    def user_data(self) -> Any:
        """Баланс и лимиты аккаунта. Бесплатный запрос."""
        return self._get("/appendix/user_data")

    # --- SERP ----------------------------------------------------------------

    def serp(self, keyword: str, location_name: str = "Ukraine", language_code: str = "ru") -> Any:
        payload = [
            {
                "keyword": keyword,
                "location_name": location_name,
                "language_code": language_code,
                "device": "desktop",
            }
        ]
        return self._post("/serp/google/organic/live/advanced", payload)

    # --- DataForSEO Labs (ключевые слова, конкуренты) -------------------------

    def ranked_keywords(self, target: str, limit: int = 50, location_name: str = "Ukraine", language_code: str = "ru") -> Any:
        payload = [
            {
                "target": target,
                "location_name": location_name,
                "language_code": language_code,
                "limit": limit,
            }
        ]
        return self._post("/dataforseo_labs/google/ranked_keywords/live", payload)

    def domain_metrics(self, target: str, location_name: str = "Ukraine", language_code: str = "ru") -> Any:
        payload = [
            {
                "target": target,
                "location_name": location_name,
                "language_code": language_code,
            }
        ]
        return self._post("/dataforseo_labs/google/domain_rank_overview/live", payload)

    def competitors(self, target: str, limit: int = 20, location_name: str = "Ukraine", language_code: str = "ru") -> Any:
        payload = [
            {
                "target": target,
                "location_name": location_name,
                "language_code": language_code,
                "limit": limit,
            }
        ]
        return self._post("/dataforseo_labs/google/competitors_domain/live", payload)

    # --- Backlinks --------------------------------------------------------

    def backlinks_summary(self, target: str) -> Any:
        payload = [{"target": target}]
        return self._post("/backlinks/summary/live", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="Проверить учётные данные и баланс")

    p_serp = sub.add_parser("serp", help="SERP по ключевому слову")
    p_serp.add_argument("keyword")
    p_serp.add_argument("--location", default="Ukraine")
    p_serp.add_argument("--language", default="ru")

    p_rk = sub.add_parser("ranked-keywords", help="Ключевые слова, по которым ранжируется домен")
    p_rk.add_argument("target")
    p_rk.add_argument("--limit", type=int, default=50)

    p_dm = sub.add_parser("domain-metrics", help="Общие метрики домена (DataForSEO Labs)")
    p_dm.add_argument("target")

    p_comp = sub.add_parser("competitors", help="Органические конкуренты домена")
    p_comp.add_argument("target")
    p_comp.add_argument("--limit", type=int, default=20)

    p_bl = sub.add_parser("backlinks-summary", help="Сводка по ссылочному профилю")
    p_bl.add_argument("target")

    args = parser.parse_args()
    client = DataForSEO()

    try:
        if args.cmd == "check":
            result = client.user_data()
        elif args.cmd == "serp":
            result = client.serp(args.keyword, args.location, args.language)
        elif args.cmd == "ranked-keywords":
            result = client.ranked_keywords(args.target, limit=args.limit)
        elif args.cmd == "domain-metrics":
            result = client.domain_metrics(args.target)
        elif args.cmd == "competitors":
            result = client.competitors(args.target, limit=args.limit)
        elif args.cmd == "backlinks-summary":
            result = client.backlinks_summary(args.target)
        else:  # pragma: no cover
            parser.error("unknown command")
            return
    except DataForSEOError as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
