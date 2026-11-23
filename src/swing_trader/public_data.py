"""Clients for free official US public-data APIs. No signals or persistence."""

from __future__ import annotations

import json
import re
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

SEC_SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
SEC_COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"
TREASURY_API_URL = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service"
BLS_API_URL = "https://api.bls.gov/publicAPI/v1/timeseries/data/"


class PublicDataError(RuntimeError):
    """Raised when an official provider cannot return valid data."""


def _request_json(request: Request) -> dict[str, Any]:
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PublicDataError(f"Public data request failed: {exc}") from exc
    if not isinstance(payload, dict):
        raise PublicDataError("Provider returned a non-object JSON response")
    return payload


def _normalize_cik(cik: str | int) -> str:
    digits = str(cik).strip()
    if not digits.isdigit() or len(digits) > 10:
        raise ValueError("CIK must contain 1 to 10 digits")
    return digits.zfill(10)


def _sec_user_agent(user_agent: str) -> dict[str, str]:
    if not user_agent.strip() or "@" not in user_agent:
        raise ValueError("SEC User-Agent must identify the application and include a contact email")
    return {"User-Agent": user_agent}


def fetch_sec_submissions(cik: str | int, *, user_agent: str) -> dict[str, Any]:
    """Fetch SEC filing history for a CIK."""
    url = SEC_SUBMISSIONS_URL.format(cik=_normalize_cik(cik))
    return _request_json(Request(url, headers={"Accept": "application/json", **_sec_user_agent(user_agent)}))


def fetch_sec_companyfacts(cik: str | int, *, user_agent: str) -> dict[str, Any]:
    """Fetch SEC XBRL company facts for a CIK."""
    url = SEC_COMPANYFACTS_URL.format(cik=_normalize_cik(cik))
    return _request_json(Request(url, headers={"Accept": "application/json", **_sec_user_agent(user_agent)}))


def fetch_treasury_dataset(
    endpoint: str,
    *,
    filters: str | None = None,
    fields: str | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    """Fetch one Fiscal Data API page; callers control pagination and request budgets."""
    clean_endpoint = endpoint.strip("/")
    if not re.fullmatch(r"v[12]/[a-zA-Z0-9_/-]+", clean_endpoint):
        raise ValueError("Invalid Treasury Fiscal Data endpoint path")
    if not 1 <= page_size <= 10000:
        raise ValueError("page_size must be between 1 and 10000")
    params: dict[str, str] = {"page[number]": "1", "page[size]": str(page_size), "format": "json"}
    if filters:
        params["filter"] = filters
    if fields:
        params["fields"] = fields
    url = f"{TREASURY_API_URL}/{clean_endpoint}?{urlencode(params)}"
    return _request_json(Request(url, headers={"Accept": "application/json"}))


def fetch_bls_series(
    series_ids: list[str], *, start_year: int, end_year: int
) -> dict[str, Any]:
    """Fetch BLS Public Data API v1 series; no key, limited public quota."""
    if not series_ids or len(series_ids) > 25:
        raise ValueError("BLS API v1 accepts between 1 and 25 series IDs per request")
    if any(not re.fullmatch(r"[A-Za-z0-9_-]+", item) for item in series_ids):
        raise ValueError("Invalid BLS series ID")
    if start_year > end_year or start_year < 1900 or end_year > 2100:
        raise ValueError("Invalid BLS year range")
    body = json.dumps(
        {"seriesid": series_ids, "startyear": str(start_year), "endyear": str(end_year)}
    ).encode("utf-8")
    request = Request(
        BLS_API_URL,
        data=body,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="POST",
    )
    payload = _request_json(request)
    if payload.get("status") != "REQUEST_SUCCEEDED":
        raise PublicDataError(f"BLS API returned status: {payload.get('status', 'unknown')}")
    return payload
