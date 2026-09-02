"""
Shared helpers for talking to the DataForSEO API.

Credentials are NEVER hardcoded here or anywhere else in this skill — they
come from the environment (DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD). If they
are not set, ask the user for their DataForSEO login (usually an email) and
password (API key) and export them for the duration of the session:

    export DATAFORSEO_LOGIN='user@example.com'
    export DATAFORSEO_PASSWORD='xxxxxxxxxxxxxxxx'

Never write real credentials into a script, a committed file, or this
skill's own source — only ever read them from the environment at run time.
"""
import json
import os
import sys
import time
import urllib.request
import urllib.error

API_BASE = "https://api.dataforseo.com/v3"


def get_credentials():
    login = os.environ.get("DATAFORSEO_LOGIN")
    password = os.environ.get("DATAFORSEO_PASSWORD")
    if not login or not password:
        sys.exit(
            "DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD are not set.\n"
            "Ask the user for their DataForSEO login (email) and password "
            "(API key), then export them before re-running this script."
        )
    return login, password


def post(endpoint, payload, retries=1, retry_wait=2):
    """POST a single-task payload (a list with exactly one task dict) to
    DataForSEO and return the parsed JSON response.

    Many DataForSEO accounts (trial tiers especially) reject multi-task
    Live/Advanced requests with 'You can set only one task at a time' — so
    every caller in this skill sends one task per request rather than
    batching. Labs/Backlinks endpoints tolerate this fine too and it keeps
    error handling uniform and per-domain/per-query failures isolated.

    A transient task-level error (DataForSEO's own 4xxxx/5xxxx status
    codes, not HTTP errors) is retried once after a short pause — we saw
    occasional 'Internal SE Server Error' on live SERP calls that succeeded
    on a plain retry.
    """
    login, password = get_credentials()
    url = f"{API_BASE}/{endpoint}"
    body = json.dumps(payload).encode("utf-8")
    last_task = None
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        import base64
        auth = base64.b64encode(f"{login}:{password}".encode()).decode()
        req.add_header("Authorization", f"Basic {auth}")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            sys.exit(f"HTTP {e.code} calling {endpoint}: {e.read().decode(errors='replace')}")
        task = (data.get("tasks") or [{}])[0]
        last_task = task
        if task.get("status_code") == 20000:
            return data
        if attempt < retries:
            time.sleep(retry_wait)
            continue
    # Ran out of retries — return what we have; caller decides whether a
    # failed task for one query/domain should abort the whole batch.
    return {"tasks": [last_task]} if last_task else {"tasks": []}


def first_result(data):
    """Pull tasks[0].result[0] out of a DataForSEO response, or None."""
    tasks = data.get("tasks") or []
    if not tasks:
        return None
    result = tasks[0].get("result")
    if not result:
        return None
    return result[0]
