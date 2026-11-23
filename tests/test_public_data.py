from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from swing_trader import public_data


def response(payload: dict) -> MagicMock:
    result = MagicMock()
    result.__enter__.return_value = result
    result.read.return_value = json.dumps(payload).encode()
    return result


def test_sec_submissions_normalizes_cik_and_sets_user_agent() -> None:
    with patch("swing_trader.public_data.urlopen", return_value=response({"name": "Example"})) as call:
        result = public_data.fetch_sec_submissions("320193", user_agent="SwingTrader admin@example.com")
    request = call.call_args.args[0]
    assert result["name"] == "Example"
    assert request.full_url.endswith("CIK0000320193.json")
    assert request.get_header("User-agent") == "SwingTrader admin@example.com"


def test_sec_rejects_bad_identity_and_cik() -> None:
    with pytest.raises(ValueError, match="User-Agent"):
        public_data.fetch_sec_submissions("320193", user_agent="SwingTrader")
    with pytest.raises(ValueError, match="CIK"):
        public_data.fetch_sec_submissions("../etc/passwd", user_agent="SwingTrader admin@example.com")


def test_sec_companyfacts_uses_official_xbrl_endpoint() -> None:
    with patch("swing_trader.public_data.urlopen", return_value=response({"facts": {}})) as call:
        public_data.fetch_sec_companyfacts(1, user_agent="SwingTrader admin@example.com")
    assert "/api/xbrl/companyfacts/CIK0000000001.json" in call.call_args.args[0].full_url


def test_treasury_dataset_builds_bounded_request() -> None:
    payload = {"data": [{"record_date": "2026-01-01"}]}
    with patch("swing_trader.public_data.urlopen", return_value=response(payload)) as call:
        result = public_data.fetch_treasury_dataset(
            "v2/accounting/od/debt_to_penny",
            filters="record_date:gte:2026-01-01",
            page_size=50,
        )
    url = call.call_args.args[0].full_url
    assert result == payload
    assert "page%5Bsize%5D=50" in url
    assert "filter=record_date%3Agte%3A2026-01-01" in url


def test_treasury_rejects_arbitrary_url_and_invalid_page_size() -> None:
    with pytest.raises(ValueError, match="endpoint"):
        public_data.fetch_treasury_dataset("https://example.com")
    with pytest.raises(ValueError, match="page_size"):
        public_data.fetch_treasury_dataset("v1/accounting/od/rates_of_exchange", page_size=0)


def test_bls_v1_posts_series_and_checks_status() -> None:
    payload = {"status": "REQUEST_SUCCEEDED", "Results": {"series": []}}
    with patch("swing_trader.public_data.urlopen", return_value=response(payload)) as call:
        result = public_data.fetch_bls_series(["LNS14000000"], start_year=2024, end_year=2026)
    request = call.call_args.args[0]
    assert result == payload
    assert json.loads(request.data)["seriesid"] == ["LNS14000000"]
    assert request.method == "POST"


def test_bls_enforces_limits_and_provider_errors() -> None:
    with pytest.raises(ValueError, match="25"):
        public_data.fetch_bls_series(["X"] * 26, start_year=2024, end_year=2025)
    with patch(
        "swing_trader.public_data.urlopen",
        return_value=response({"status": "REQUEST_NOT_PROCESSED"}),
    ):
        with pytest.raises(public_data.PublicDataError, match="REQUEST_NOT_PROCESSED"):
            public_data.fetch_bls_series(["LNS14000000"], start_year=2024, end_year=2025)
