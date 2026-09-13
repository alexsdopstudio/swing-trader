from __future__ import annotations

import hashlib
import json
import math
import os
import re
import uuid
import zipfile
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import yaml

from .daily_scan_recorder import ARTIFACT_ID, verify_daily_scan_archive
from .execution import ExecutionCostModel, load_execution_cost_models
from .portfolio import PortfolioBacktestConfig
from .risk import initial_stop, position_plan_for_risk, trailing_stop


OPERATIONS_SCHEMA_VERSION = 1
LEDGER_SCHEMA_VERSION = 1
PAPER_MODE = "paper"
ENTRY_TIMING = "next_available_open_after_signal"
_ARCHIVE_PATTERN = re.compile(r"^daily-scan-history-(\d{4}-\d{2}-\d{2})-([0-9a-f]{64})\.zip$")
DECISIONS = frozenset({"approved", "declined", "deferred"})
EXIT_REASONS = frozenset({"initial_stop", "trailing_stop", "operator_recorded"})


@dataclass(frozen=True)
class PaperOperationsConfig:
    """Personal paper-operations settings with frozen v1 risk controls."""

    path: Path
    config_sha256: str
    cost_config_path: Path
    cost_config_sha256: str
    starting_equity: float
    currency: str
    portfolio: PortfolioBacktestConfig


@dataclass(frozen=True)
class ScanObservationRow:
    symbol: str
    asset_class: str
    score: int
    signal: str
    close: float
    atr14: float
    signal_date: date


@dataclass(frozen=True)
class DailyScanObservation:
    archive_path: Path
    archive_sha256: str
    observation_date: date
    scanner_config_sha256: str
    recorder_code_sha: str
    rows: tuple[ScanObservationRow, ...]


@dataclass(frozen=True)
class PaperTicket:
    """A deterministic planning ticket, not an order or a promised fill."""

    schema_version: int
    ticket_id: str
    ticket_sha256: str
    archive_sha256: str
    scanner_config_sha256: str
    operations_config_sha256: str
    cost_config_sha256: str
    observation_date: str
    signal_date: str
    symbol: str
    asset_class: str
    score: int
    planning_reference: float
    expected_entry_fill: float
    atr14: float
    initial_stop: float
    trailing_atr: float
    planned_units: float
    planned_notional: float
    risk_per_unit: float
    planned_initial_loss: float
    planning_equity: float
    planning_cash: float
    planning_open_risk: float
    currency: str
    entry_timing: str = ENTRY_TIMING


@dataclass(frozen=True)
class PaperPosition:
    ticket: PaperTicket
    entry_date: date
    entry_reference: float
    entry_fill: float
    entry_fee: float
    units: float
    initial_stop: float
    risk_per_unit: float
    initial_loss: float


@dataclass(frozen=True)
class MarkedPaperPosition:
    position: PaperPosition
    current_stop: float
    highest_close: float | None
    last_mark_date: date | None


@dataclass(frozen=True)
class PaperLedgerState:
    events: tuple[dict[str, Any], ...]
    tickets: dict[str, PaperTicket]
    decisions: dict[str, str]
    positions: dict[str, PaperPosition]
    closed_ticket_ids: frozenset[str]
    cash: float


@dataclass(frozen=True)
class PaperAccountState:
    cash: float
    equity: float
    open_risk: float
    marked_positions: tuple[MarkedPaperPosition, ...]


@dataclass(frozen=True)
class BriefCandidate:
    symbol: str
    asset_class: str
    score: int
    signal: str
    signal_date: date
    status: str
    reason: str | None
    ticket: PaperTicket | None


@dataclass(frozen=True)
class DailyBrief:
    observation: DailyScanObservation
    config: PaperOperationsConfig
    account: PaperAccountState
    candidates: tuple[BriefCandidate, ...]


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _finite_number(value: Any, label: str, *, positive: bool = False) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be a number")
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be a number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{label} must be finite")
    if positive and number <= 0:
        raise ValueError(f"{label} must be positive")
    return number


def _strict_date(value: Any, label: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO date")
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO date") from exc
    if parsed.isoformat() != value:
        raise ValueError(f"{label} must be an ISO date")
    return parsed


def _strict_timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be an ISO UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO UTC timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(UTC)


def _timestamp_text(value: datetime | None) -> str:
    if value is not None and value.tzinfo is None:
        raise ValueError("event_at must include a timezone")
    timestamp = (value or datetime.now(UTC)).astimezone(UTC)
    return timestamp.isoformat().replace("+00:00", "Z")


def _require_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a mapping")
    return value


def _require_exact_keys(payload: dict[str, Any], expected: set[str], label: str) -> None:
    observed = set(payload)
    if observed != expected:
        missing = sorted(expected.difference(observed))
        extra = sorted(observed.difference(expected))
        details = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if extra:
            details.append("unexpected " + ", ".join(extra))
        raise ValueError(f"{label} has invalid fields: {'; '.join(details)}")


def load_paper_operations_config(path: str | Path) -> PaperOperationsConfig:
    """Load the narrow local configuration for approval-only paper operations."""
    config_path = Path(path).resolve()
    raw_bytes = config_path.read_bytes()
    raw = _require_mapping(yaml.safe_load(raw_bytes) or {}, "paper operations config")
    _require_exact_keys(
        raw,
        {
            "schema_version",
            "mode",
            "approval_required",
            "account",
            "execution_costs_path",
        },
        "paper operations config",
    )
    if raw["schema_version"] != OPERATIONS_SCHEMA_VERSION:
        raise ValueError("unsupported paper operations config schema")
    if raw["mode"] != PAPER_MODE:
        raise ValueError("paper operations mode must be 'paper'")
    if raw["approval_required"] is not True:
        raise ValueError("paper operations must require explicit human approval")

    account = _require_mapping(raw["account"], "paper operations account")
    _require_exact_keys(account, {"starting_equity", "currency"}, "paper operations account")
    starting_equity = _finite_number(account["starting_equity"], "starting_equity", positive=True)
    currency = account["currency"]
    if not isinstance(currency, str) or re.fullmatch(r"[A-Z]{3}", currency) is None:
        raise ValueError("account currency must be a three-letter uppercase code")

    raw_cost_path = raw["execution_costs_path"]
    if not isinstance(raw_cost_path, str) or not raw_cost_path:
        raise ValueError("execution_costs_path must be a non-empty string")
    cost_path = Path(raw_cost_path)
    if not cost_path.is_absolute():
        cost_path = config_path.parent / cost_path
    cost_path = cost_path.resolve()
    cost_bytes = cost_path.read_bytes()
    cost_models = load_execution_cost_models(cost_path)
    portfolio = PortfolioBacktestConfig(
        initial_equity=starting_equity,
        cost_models=cost_models,
    )
    return PaperOperationsConfig(
        path=config_path,
        config_sha256=_sha256(raw_bytes),
        cost_config_path=cost_path,
        cost_config_sha256=_sha256(cost_bytes),
        starting_equity=starting_equity,
        currency=currency,
        portfolio=portfolio,
    )


def load_daily_scan_observation(path: str | Path) -> DailyScanObservation:
    """Load only a verified, operational-only daily scanner archive."""
    archive_path = Path(path).resolve()
    manifest = verify_daily_scan_archive(archive_path)
    match = _ARCHIVE_PATTERN.match(archive_path.name)
    if match is None:
        raise ValueError("daily scan archive filename does not match the required digest format")
    observation_date = _strict_date(match.group(1), "daily scan archive observation date")
    archive_sha256 = match.group(2)
    capture = _require_mapping(manifest.get("capture"), "daily scan archive capture")
    if _strict_date(capture.get("observation_date"), "manifest observation date") != observation_date:
        raise RuntimeError("manifest observation date does not match the archive filename")
    integrity = _require_mapping(
        manifest.get("research_integrity"), "daily scan archive research_integrity"
    )
    if integrity.get("validation_evidence") is not False:
        raise RuntimeError("paper operations require non-validation daily scanner observations")
    if integrity.get("holdout_substitution_allowed") is not False:
        raise RuntimeError("paper operations cannot use holdout-substitution evidence")

    universe = _require_mapping(manifest.get("universe"), "daily scan archive universe")
    scanner_config_sha256 = universe.get("config_sha256")
    if not isinstance(scanner_config_sha256, str) or len(scanner_config_sha256) != 64:
        raise RuntimeError("daily scan archive has an invalid universe config digest")
    outputs = _require_mapping(manifest.get("outputs"), "daily scan archive outputs")
    json_record = _require_mapping(outputs.get("json"), "daily scan archive JSON output")
    result_path = json_record.get("path")
    if not isinstance(result_path, str):
        raise RuntimeError("daily scan archive has no JSON result path")

    with zipfile.ZipFile(archive_path, "r") as archive:
        raw_rows = json.loads(archive.read(result_path))
    if not isinstance(raw_rows, list):
        raise RuntimeError("daily scan results must be a list")
    source = _require_mapping(manifest.get("source"), "daily scan archive source")
    rows: list[ScanObservationRow] = []
    symbols: set[str] = set()
    for index, raw_row in enumerate(raw_rows, start=1):
        row = _require_mapping(raw_row, f"daily scan result {index}")
        symbol = row.get("symbol")
        asset_class = row.get("asset_class")
        score = row.get("score")
        signal = row.get("signal")
        if not isinstance(symbol, str) or not symbol:
            raise RuntimeError(f"daily scan result {index} has an invalid symbol")
        if symbol in symbols:
            raise RuntimeError(f"daily scan results contain duplicate symbol {symbol}")
        symbols.add(symbol)
        if not isinstance(asset_class, str) or not asset_class:
            raise RuntimeError(f"daily scan result {symbol} has an invalid asset class")
        if isinstance(score, bool) or not isinstance(score, int):
            raise RuntimeError(f"daily scan result {symbol} has an invalid score")
        if signal not in {"BUY", "WATCH"}:
            raise RuntimeError(f"daily scan result {symbol} has an invalid signal")
        source_record = _require_mapping(source.get(symbol), f"daily scan source for {symbol}")
        signal_date = _strict_date(source_record.get("last_observation"), f"signal date for {symbol}")
        rows.append(
            ScanObservationRow(
                symbol=symbol,
                asset_class=asset_class,
                score=score,
                signal=signal,
                close=_finite_number(row.get("close"), f"daily scan close for {symbol}", positive=True),
                atr14=_finite_number(row.get("atr14"), f"daily scan ATR for {symbol}", positive=True),
                signal_date=signal_date,
            )
        )

    recorder_code_sha = capture.get("recorder_code_sha")
    if not isinstance(recorder_code_sha, str) or not recorder_code_sha:
        raise RuntimeError("daily scan archive has an invalid recorder code SHA")
    return DailyScanObservation(
        archive_path=archive_path,
        archive_sha256=archive_sha256,
        observation_date=observation_date,
        scanner_config_sha256=scanner_config_sha256,
        recorder_code_sha=recorder_code_sha,
        rows=tuple(rows),
    )


def _ticket_identity(
    observation: DailyScanObservation,
    row: ScanObservationRow,
    config: PaperOperationsConfig,
) -> str:
    identity = {
        "archive_sha256": observation.archive_sha256,
        "cost_config_sha256": config.cost_config_sha256,
        "operations_config_sha256": config.config_sha256,
        "scanner_config_sha256": observation.scanner_config_sha256,
        "schema_version": OPERATIONS_SCHEMA_VERSION,
        "signal_date": row.signal_date.isoformat(),
        "symbol": row.symbol,
    }
    return "PT-" + _sha256(_canonical_json(identity))[:20]


def _ticket_payload_without_digest(ticket: PaperTicket) -> dict[str, Any]:
    payload = asdict(ticket)
    payload.pop("ticket_sha256")
    return payload


def _ticket_digest(ticket: PaperTicket) -> str:
    return _sha256(_canonical_json(_ticket_payload_without_digest(ticket)))


def _ticket_from_payload(payload: Any) -> PaperTicket:
    raw = _require_mapping(payload, "ticket")
    fields = set(PaperTicket.__dataclass_fields__)
    _require_exact_keys(raw, fields, "ticket")
    ticket = PaperTicket(
        schema_version=raw["schema_version"],
        ticket_id=raw["ticket_id"],
        ticket_sha256=raw["ticket_sha256"],
        archive_sha256=raw["archive_sha256"],
        scanner_config_sha256=raw["scanner_config_sha256"],
        operations_config_sha256=raw["operations_config_sha256"],
        cost_config_sha256=raw["cost_config_sha256"],
        observation_date=raw["observation_date"],
        signal_date=raw["signal_date"],
        symbol=raw["symbol"],
        asset_class=raw["asset_class"],
        score=raw["score"],
        planning_reference=_finite_number(raw["planning_reference"], "ticket planning_reference", positive=True),
        expected_entry_fill=_finite_number(
            raw["expected_entry_fill"], "ticket expected_entry_fill", positive=True
        ),
        atr14=_finite_number(raw["atr14"], "ticket atr14", positive=True),
        initial_stop=_finite_number(raw["initial_stop"], "ticket initial_stop", positive=True),
        trailing_atr=_finite_number(raw["trailing_atr"], "ticket trailing_atr", positive=True),
        planned_units=_finite_number(raw["planned_units"], "ticket planned_units", positive=True),
        planned_notional=_finite_number(raw["planned_notional"], "ticket planned_notional", positive=True),
        risk_per_unit=_finite_number(raw["risk_per_unit"], "ticket risk_per_unit", positive=True),
        planned_initial_loss=_finite_number(
            raw["planned_initial_loss"], "ticket planned_initial_loss", positive=True
        ),
        planning_equity=_finite_number(raw["planning_equity"], "ticket planning_equity", positive=True),
        planning_cash=_finite_number(raw["planning_cash"], "ticket planning_cash"),
        planning_open_risk=_finite_number(
            raw["planning_open_risk"], "ticket planning_open_risk"
        ),
        currency=raw["currency"],
        entry_timing=raw["entry_timing"],
    )
    _validate_ticket(ticket)
    return ticket


def _validate_ticket(ticket: PaperTicket) -> None:
    if ticket.schema_version != OPERATIONS_SCHEMA_VERSION:
        raise ValueError("unsupported paper ticket schema")
    if not isinstance(ticket.ticket_id, str) or not re.fullmatch(r"PT-[0-9a-f]{20}", ticket.ticket_id):
        raise ValueError("paper ticket id is invalid")
    for label, value in (
        ("archive_sha256", ticket.archive_sha256),
        ("scanner_config_sha256", ticket.scanner_config_sha256),
        ("operations_config_sha256", ticket.operations_config_sha256),
        ("cost_config_sha256", ticket.cost_config_sha256),
        ("ticket_sha256", ticket.ticket_sha256),
    ):
        if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
            raise ValueError(f"paper ticket {label} is invalid")
    if not isinstance(ticket.symbol, str) or not ticket.symbol:
        raise ValueError("paper ticket symbol is invalid")
    if not isinstance(ticket.asset_class, str) or not ticket.asset_class:
        raise ValueError("paper ticket asset_class is invalid")
    if isinstance(ticket.score, bool) or not isinstance(ticket.score, int):
        raise ValueError("paper ticket score is invalid")
    _strict_date(ticket.observation_date, "paper ticket observation_date")
    _strict_date(ticket.signal_date, "paper ticket signal_date")
    if ticket.entry_timing != ENTRY_TIMING:
        raise ValueError("paper ticket execution timing is invalid")
    if re.fullmatch(r"[A-Z]{3}", ticket.currency or "") is None:
        raise ValueError("paper ticket currency is invalid")
    if ticket.initial_stop >= ticket.expected_entry_fill:
        raise ValueError("paper ticket initial stop must be below its expected entry fill")
    for label, value, positive in (
        ("planning_reference", ticket.planning_reference, True),
        ("expected_entry_fill", ticket.expected_entry_fill, True),
        ("atr14", ticket.atr14, True),
        ("initial_stop", ticket.initial_stop, True),
        ("trailing_atr", ticket.trailing_atr, True),
        ("planned_units", ticket.planned_units, True),
        ("planned_notional", ticket.planned_notional, True),
        ("risk_per_unit", ticket.risk_per_unit, True),
        ("planned_initial_loss", ticket.planned_initial_loss, True),
        ("planning_equity", ticket.planning_equity, True),
        ("planning_cash", ticket.planning_cash, False),
        ("planning_open_risk", ticket.planning_open_risk, False),
    ):
        _finite_number(value, f"paper ticket {label}", positive=positive)
    if ticket.planning_cash < 0 or ticket.planning_open_risk < 0:
        raise ValueError("paper ticket planning cash and open risk cannot be negative")
    if ticket.ticket_sha256 != _ticket_digest(ticket):
        raise ValueError("paper ticket digest does not match its contents")


def _require_ticket_config(ticket: PaperTicket, config: PaperOperationsConfig) -> None:
    _validate_ticket(ticket)
    if ticket.operations_config_sha256 != config.config_sha256:
        raise ValueError("ticket provenance does not match the active paper operations config")
    if ticket.cost_config_sha256 != config.cost_config_sha256:
        raise ValueError("ticket provenance does not match the active execution-cost config")
    if ticket.currency != config.currency:
        raise ValueError("ticket provenance does not match the active account currency")


def _ticket_observation_key(ticket: PaperTicket) -> tuple[str, str, str]:
    return ticket.archive_sha256, ticket.symbol, ticket.signal_date


def _cost_model(ticket: PaperTicket, config: PaperOperationsConfig) -> ExecutionCostModel:
    return config.portfolio.cost_model_for(ticket.asset_class)


def _position_open_risk(position: PaperPosition, config: PaperOperationsConfig) -> float:
    model = _cost_model(position.ticket, config)
    return model.long_risk_per_unit(position.entry_fill, position.initial_stop) * position.units


def _conservative_entry_equity(
    cash: float,
    positions: dict[str, PaperPosition],
    config: PaperOperationsConfig,
) -> float:
    """Value existing paper positions at their expected non-gap stop proceeds for sizing."""
    equity = cash
    for position in positions.values():
        model = _cost_model(position.ticket, config)
        equity += position.units * model.sell_net_per_unit(position.initial_stop)
    return equity


def _entry_plan(
    ticket: PaperTicket,
    entry_reference: float,
    *,
    cash: float,
    positions: dict[str, PaperPosition],
    config: PaperOperationsConfig,
) -> dict[str, float]:
    """Re-price an approved paper candidate while retaining frozen v1 risk rules."""
    _require_ticket_config(ticket, config)
    reference = _finite_number(entry_reference, "entry_reference", positive=True)
    if ticket.symbol in positions:
        raise ValueError(f"paper position already exists for {ticket.symbol}")
    if len(positions) >= config.portfolio.max_positions:
        raise ValueError("paper entry is blocked by the maximum-position limit")

    model = _cost_model(ticket, config)
    entry_fill = model.buy_fill(reference)
    stop = initial_stop(entry_fill, ticket.atr14, config.portfolio.stop_atr)
    if stop <= 0:
        raise ValueError("paper entry initial stop is not positive")
    risk_per_unit = model.long_risk_per_unit(entry_fill, stop)
    if risk_per_unit <= 0:
        raise ValueError("paper entry risk per unit is not positive")

    conservative_equity = _conservative_entry_equity(cash, positions, config)
    sizing_equity = min(ticket.planning_equity, conservative_equity)
    if not math.isfinite(sizing_equity) or sizing_equity <= 0:
        raise ValueError("paper entry has no positive conservative account equity")
    open_risk = sum(_position_open_risk(position, config) for position in positions.values())
    remaining_risk = max(
        0.0,
        sizing_equity * config.portfolio.max_open_risk_fraction - open_risk,
    )
    plan = position_plan_for_risk(
        equity=sizing_equity,
        entry=entry_fill,
        stop=stop,
        risk_per_unit=risk_per_unit,
        risk_fraction=config.portfolio.risk_fraction,
        max_position_fraction=config.portfolio.max_position_fraction,
    )
    units_by_cash = max(0.0, cash / model.buy_cash_per_unit(reference))
    units_by_open_risk = remaining_risk / risk_per_unit
    units = min(plan.units, units_by_cash, units_by_open_risk)
    if not math.isfinite(units) or units <= 0:
        raise ValueError("paper entry is blocked by available cash or aggregate open-risk limits")

    entry_notional = units * entry_fill
    entry_fee = model.commission(entry_notional)
    return {
        "entry_fee": entry_fee,
        "entry_fill": entry_fill,
        "initial_loss": units * risk_per_unit,
        "initial_stop": stop,
        "risk_per_unit": risk_per_unit,
        "sizing_equity": sizing_equity,
        "units": units,
    }


def _read_ledger_events(path: str | Path) -> list[dict[str, Any]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return []
    if not ledger_path.is_file():
        raise ValueError(f"paper ledger path is not a file: {ledger_path}")
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(ledger_path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            raise ValueError(f"paper ledger has an empty line at {line_number}")
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"paper ledger has invalid JSON at line {line_number}") from exc
        if not isinstance(event, dict):
            raise ValueError(f"paper ledger event {line_number} must be an object")
        events.append(event)
    return events


def _validate_event_envelope(event: dict[str, Any], sequence: int) -> tuple[str, datetime]:
    base_fields = {"schema_version", "sequence", "event_id", "event_type", "event_at_utc"}
    event_type = event.get("event_type")
    if event_type in DECISIONS:
        allowed = base_fields | {"ticket", "note"}
    elif event_type == "entry_recorded":
        allowed = base_fields | {
            "ticket_id",
            "source",
            "execution_date",
            "entry_reference",
            "paper_fill",
            "entry_fee",
            "units",
            "initial_stop",
            "risk_per_unit",
            "initial_loss",
            "sizing_equity",
        }
    elif event_type == "exit_recorded":
        allowed = base_fields | {
            "ticket_id",
            "source",
            "execution_date",
            "exit_reference",
            "paper_fill",
            "exit_fee",
            "units",
            "reason",
            "gross_pnl",
            "net_pnl",
        }
    else:
        raise ValueError("paper ledger event has an unsupported event_type")
    if set(event).difference(allowed):
        raise ValueError("paper ledger event has unexpected fields")
    if not base_fields.issubset(event):
        raise ValueError("paper ledger event is missing envelope fields")
    if event.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise ValueError("paper ledger event has an unsupported schema")
    if event.get("sequence") != sequence:
        raise ValueError("paper ledger event sequence is not append-only")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or re.fullmatch(r"[0-9a-f]{32}", event_id) is None:
        raise ValueError("paper ledger event_id is invalid")
    return event_id, _strict_timestamp(event.get("event_at_utc"), "paper ledger event_at_utc")


def _event_float(event: dict[str, Any], field: str, *, positive: bool = False) -> float:
    if field not in event:
        raise ValueError(f"paper ledger event is missing {field}")
    return _finite_number(event[field], f"paper ledger {field}", positive=positive)


def _match_value(observed: float, expected: float, label: str) -> None:
    if not math.isclose(observed, expected, rel_tol=1e-12, abs_tol=1e-10):
        raise ValueError(f"paper ledger {label} does not match deterministic paper calculations")


def load_paper_ledger(
    path: str | Path,
    config: PaperOperationsConfig,
) -> PaperLedgerState:
    """Validate an append-only ledger and derive its paper cash and open positions."""
    events = _read_ledger_events(path)
    tickets: dict[str, PaperTicket] = {}
    decisions: dict[str, str] = {}
    positions: dict[str, PaperPosition] = {}
    closed_ticket_ids: set[str] = set()
    ticket_keys: set[tuple[str, str, str]] = set()
    entered_ticket_ids: set[str] = set()
    seen_event_ids: set[str] = set()
    cash = config.starting_equity
    previous_timestamp: datetime | None = None

    for sequence, event in enumerate(events, start=1):
        event_id, event_timestamp = _validate_event_envelope(event, sequence)
        if event_id in seen_event_ids:
            raise ValueError("paper ledger contains a duplicate event_id")
        seen_event_ids.add(event_id)
        if previous_timestamp is not None and event_timestamp < previous_timestamp:
            raise ValueError("paper ledger event timestamps are out of order")
        previous_timestamp = event_timestamp
        event_type = event["event_type"]

        if event_type in DECISIONS:
            ticket = _ticket_from_payload(event.get("ticket"))
            _require_ticket_config(ticket, config)
            if ticket.ticket_id in tickets:
                raise ValueError("paper ledger contains a duplicate ticket decision")
            observation_key = _ticket_observation_key(ticket)
            if observation_key in ticket_keys:
                raise ValueError("paper ledger contains duplicate ticket provenance")
            note = event.get("note")
            if note is not None and (not isinstance(note, str) or not note.strip()):
                raise ValueError("paper ledger note must be a non-empty string when supplied")
            tickets[ticket.ticket_id] = ticket
            ticket_keys.add(observation_key)
            decisions[ticket.ticket_id] = event_type
            continue

        ticket_id = event.get("ticket_id")
        if not isinstance(ticket_id, str) or ticket_id not in tickets:
            raise ValueError("paper ledger event references an unknown ticket")
        ticket = tickets[ticket_id]
        if event.get("source") != PAPER_MODE:
            raise ValueError("paper ledger supports paper fills only")

        if event_type == "entry_recorded":
            if decisions[ticket_id] != "approved":
                raise ValueError("paper entry requires a prior approved ticket")
            if ticket_id in entered_ticket_ids:
                raise ValueError("paper ledger contains a duplicate entry for a ticket")
            execution_date = _strict_date(event.get("execution_date"), "paper entry execution_date")
            if execution_date <= _strict_date(ticket.signal_date, "ticket signal_date"):
                raise ValueError("paper entry cannot execute on the signal date or earlier")
            entry_reference = _event_float(event, "entry_reference", positive=True)
            plan = _entry_plan(
                ticket,
                entry_reference,
                cash=cash,
                positions=positions,
                config=config,
            )
            for field, expected in plan.items():
                event_field = "paper_fill" if field == "entry_fill" else field
                _match_value(
                    _event_float(event, event_field, positive=field != "entry_fee"),
                    expected,
                    event_field,
                )
            position = PaperPosition(
                ticket=ticket,
                entry_date=execution_date,
                entry_reference=entry_reference,
                entry_fill=plan["entry_fill"],
                entry_fee=plan["entry_fee"],
                units=plan["units"],
                initial_stop=plan["initial_stop"],
                risk_per_unit=plan["risk_per_unit"],
                initial_loss=plan["initial_loss"],
            )
            if ticket.symbol in positions:
                raise ValueError(f"paper ledger already has an open position for {ticket.symbol}")
            cash -= position.entry_fill * position.units + position.entry_fee
            if cash < -1e-9:
                raise ValueError("paper ledger entry would make cash negative")
            entered_ticket_ids.add(ticket_id)
            positions[ticket.symbol] = position
            continue

        if ticket_id not in entered_ticket_ids:
            raise ValueError("paper exit requires a prior paper entry")
        position = positions.get(ticket.symbol)
        if position is None:
            raise ValueError("paper ledger contains a duplicate or out-of-order exit")
        execution_date = _strict_date(event.get("execution_date"), "paper exit execution_date")
        if execution_date < position.entry_date:
            raise ValueError("paper exit cannot precede the paper entry date")
        exit_reference = _event_float(event, "exit_reference", positive=True)
        units = _event_float(event, "units", positive=True)
        _match_value(units, position.units, "exit units")
        reason = event.get("reason")
        if reason not in EXIT_REASONS:
            raise ValueError("paper exit reason is invalid")
        model = _cost_model(ticket, config)
        exit_fill = model.sell_fill(exit_reference)
        exit_fee = model.commission(exit_fill * position.units)
        gross_pnl = (exit_fill - position.entry_fill) * position.units
        net_pnl = gross_pnl - position.entry_fee - exit_fee
        _match_value(_event_float(event, "paper_fill", positive=True), exit_fill, "paper exit fill")
        _match_value(_event_float(event, "exit_fee"), exit_fee, "paper exit fee")
        _match_value(_event_float(event, "gross_pnl"), gross_pnl, "paper exit gross_pnl")
        _match_value(_event_float(event, "net_pnl"), net_pnl, "paper exit net_pnl")
        cash += exit_fill * position.units - exit_fee
        positions.pop(ticket.symbol)
        closed_ticket_ids.add(ticket_id)

    return PaperLedgerState(
        events=tuple(events),
        tickets=tickets,
        decisions=decisions,
        positions=positions,
        closed_ticket_ids=frozenset(closed_ticket_ids),
        cash=cash,
    )


def _new_event(
    state: PaperLedgerState,
    event_type: str,
    *,
    event_id: str | None,
    event_at: datetime | None,
) -> dict[str, Any]:
    identifier = event_id or uuid.uuid4().hex
    if re.fullmatch(r"[0-9a-f]{32}", identifier) is None:
        raise ValueError("event_id must be a 32-character lowercase hexadecimal string")
    if any(event.get("event_id") == identifier for event in state.events):
        raise ValueError("paper ledger already contains this event_id")
    timestamp = _timestamp_text(event_at)
    if state.events:
        previous = _strict_timestamp(state.events[-1].get("event_at_utc"), "paper ledger event_at_utc")
        if _strict_timestamp(timestamp, "event_at") < previous:
            raise ValueError("paper ledger event timestamps must remain append-only")
    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "sequence": len(state.events) + 1,
        "event_id": identifier,
        "event_type": event_type,
        "event_at_utc": timestamp,
    }


def _append_event(path: str | Path, event: dict[str, Any]) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    with ledger_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, allow_nan=False, separators=(",", ":"), sort_keys=True))
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def record_decision(
    path: str | Path,
    config: PaperOperationsConfig,
    ticket: PaperTicket,
    decision: str,
    *,
    note: str | None = None,
    event_id: str | None = None,
    event_at: datetime | None = None,
) -> dict[str, Any]:
    """Append one explicit human decision without mutating any earlier ledger event."""
    if decision not in DECISIONS:
        raise ValueError("decision must be approved, declined, or deferred")
    _require_ticket_config(ticket, config)
    state = load_paper_ledger(path, config)
    if ticket.ticket_id in state.tickets:
        raise ValueError("paper ticket already has a human decision")
    if _ticket_observation_key(ticket) in {
        _ticket_observation_key(existing) for existing in state.tickets.values()
    }:
        raise ValueError("paper ticket provenance already has a human decision")
    if note is not None and not note.strip():
        raise ValueError("decision note must be non-empty when supplied")
    event = _new_event(state, decision, event_id=event_id, event_at=event_at)
    event["ticket"] = asdict(ticket)
    if note is not None:
        event["note"] = note
    _append_event(path, event)
    return event


def record_paper_entry(
    path: str | Path,
    config: PaperOperationsConfig,
    ticket_id: str,
    execution_date: str | date,
    entry_reference: float,
    *,
    event_id: str | None = None,
    event_at: datetime | None = None,
) -> dict[str, Any]:
    """Append a deterministic paper fill after an explicit approval; no order is sent."""
    state = load_paper_ledger(path, config)
    ticket = state.tickets.get(ticket_id)
    if ticket is None:
        raise ValueError("paper entry references an unknown ticket")
    if state.decisions[ticket_id] != "approved":
        raise ValueError("paper entry requires a prior approved ticket")
    date_text = execution_date.isoformat() if isinstance(execution_date, date) else execution_date
    parsed_date = _strict_date(date_text, "paper entry execution_date")
    if parsed_date <= _strict_date(ticket.signal_date, "ticket signal_date"):
        raise ValueError("paper entry cannot execute on the signal date or earlier")
    plan = _entry_plan(
        ticket,
        entry_reference,
        cash=state.cash,
        positions=state.positions,
        config=config,
    )
    event = _new_event(state, "entry_recorded", event_id=event_id, event_at=event_at)
    event.update(
        {
            "ticket_id": ticket_id,
            "source": PAPER_MODE,
            "execution_date": parsed_date.isoformat(),
            "entry_reference": float(entry_reference),
            "paper_fill": plan["entry_fill"],
            "entry_fee": plan["entry_fee"],
            "units": plan["units"],
            "initial_stop": plan["initial_stop"],
            "risk_per_unit": plan["risk_per_unit"],
            "initial_loss": plan["initial_loss"],
            "sizing_equity": plan["sizing_equity"],
        }
    )
    _append_event(path, event)
    return event


def record_paper_exit(
    path: str | Path,
    config: PaperOperationsConfig,
    ticket_id: str,
    execution_date: str | date,
    exit_reference: float,
    reason: str,
    *,
    event_id: str | None = None,
    event_at: datetime | None = None,
) -> dict[str, Any]:
    """Append a full paper exit record; no venue, credential, or order adapter is used."""
    if reason not in EXIT_REASONS:
        raise ValueError("paper exit reason is invalid")
    state = load_paper_ledger(path, config)
    ticket = state.tickets.get(ticket_id)
    if ticket is None:
        raise ValueError("paper exit references an unknown ticket")
    position = state.positions.get(ticket.symbol)
    if position is None or position.ticket.ticket_id != ticket_id:
        raise ValueError("paper exit requires an open position for its ticket")
    date_text = execution_date.isoformat() if isinstance(execution_date, date) else execution_date
    parsed_date = _strict_date(date_text, "paper exit execution_date")
    if parsed_date < position.entry_date:
        raise ValueError("paper exit cannot precede the paper entry date")
    reference = _finite_number(exit_reference, "exit_reference", positive=True)
    model = _cost_model(ticket, config)
    paper_fill = model.sell_fill(reference)
    exit_fee = model.commission(paper_fill * position.units)
    gross_pnl = (paper_fill - position.entry_fill) * position.units
    net_pnl = gross_pnl - position.entry_fee - exit_fee
    event = _new_event(state, "exit_recorded", event_id=event_id, event_at=event_at)
    event.update(
        {
            "ticket_id": ticket_id,
            "source": PAPER_MODE,
            "execution_date": parsed_date.isoformat(),
            "exit_reference": reference,
            "paper_fill": paper_fill,
            "exit_fee": exit_fee,
            "units": position.units,
            "reason": reason,
            "gross_pnl": gross_pnl,
            "net_pnl": net_pnl,
        }
    )
    _append_event(path, event)
    return event


def _load_history(
    observation: DailyScanObservation,
    archive_dir: str | Path | None,
) -> tuple[DailyScanObservation, ...]:
    observations: dict[date, DailyScanObservation] = {}
    if archive_dir is not None:
        directory = Path(archive_dir)
        if not directory.exists():
            raise FileNotFoundError(f"daily scan archive directory does not exist: {directory}")
        for archive_path in sorted(directory.glob(f"{ARTIFACT_ID}-*.zip")):
            loaded = load_daily_scan_observation(archive_path)
            if loaded.observation_date > observation.observation_date:
                continue
            previous = observations.get(loaded.observation_date)
            if previous is not None and previous.archive_sha256 != loaded.archive_sha256:
                raise ValueError("daily scan archive history contains duplicate observation dates")
            observations[loaded.observation_date] = loaded
    previous = observations.get(observation.observation_date)
    if previous is not None and previous.archive_sha256 != observation.archive_sha256:
        raise ValueError("current daily scan archive conflicts with supplied archive history")
    observations[observation.observation_date] = observation
    return tuple(observations[key] for key in sorted(observations))


def _mark_positions(
    state: PaperLedgerState,
    observation: DailyScanObservation,
    archive_dir: str | Path | None,
) -> tuple[MarkedPaperPosition, ...]:
    history = _load_history(observation, archive_dir)
    earliest_observation = history[0].observation_date
    rows_by_symbol: dict[str, list[ScanObservationRow]] = {}
    for archive in history:
        for row in archive.rows:
            rows_by_symbol.setdefault(row.symbol, []).append(row)

    marked: list[MarkedPaperPosition] = []
    for symbol, position in sorted(state.positions.items()):
        if position.entry_date < earliest_observation:
            raise ValueError(
                f"cannot reconstruct trailing stop for {symbol}; provide scan archives from its entry date"
            )
        seen_signal_dates: set[date] = set()
        current_stop = position.initial_stop
        highest_close: float | None = None
        last_mark_date: date | None = None
        for row in sorted(rows_by_symbol.get(symbol, []), key=lambda item: item.signal_date):
            if row.signal_date < position.entry_date or row.signal_date in seen_signal_dates:
                continue
            seen_signal_dates.add(row.signal_date)
            highest_close = row.close if highest_close is None else max(highest_close, row.close)
            current_stop = trailing_stop(
                current_stop,
                highest_close,
                row.atr14,
                position.ticket.trailing_atr,
            )
            last_mark_date = row.signal_date
        marked.append(
            MarkedPaperPosition(
                position=position,
                current_stop=current_stop,
                highest_close=highest_close,
                last_mark_date=last_mark_date,
            )
        )
    return tuple(marked)


def _account_state(
    state: PaperLedgerState,
    observation: DailyScanObservation,
    archive_dir: str | Path | None,
    config: PaperOperationsConfig,
) -> PaperAccountState:
    marked_positions = _mark_positions(state, observation, archive_dir)
    rows = {row.symbol: row for row in observation.rows}
    equity = state.cash
    open_risk = 0.0
    for marked in marked_positions:
        position = marked.position
        row = rows.get(position.ticket.symbol)
        if row is None:
            raise ValueError(f"current daily scan archive cannot mark open position {position.ticket.symbol}")
        equity += position.units * row.close
        model = _cost_model(position.ticket, config)
        open_risk += model.long_risk_per_unit(position.entry_fill, marked.current_stop) * position.units
    if not math.isfinite(equity) or equity <= 0:
        raise ValueError("paper account equity must remain positive")
    return PaperAccountState(
        cash=state.cash,
        equity=equity,
        open_risk=open_risk,
        marked_positions=marked_positions,
    )


def _new_ticket(
    observation: DailyScanObservation,
    row: ScanObservationRow,
    config: PaperOperationsConfig,
    *,
    planning_equity: float,
    planning_cash: float,
    planning_open_risk: float,
) -> tuple[PaperTicket | None, str | None]:
    if row.score < config.portfolio.min_score:
        return None, "score_below_frozen_v1_minimum"
    model = config.portfolio.cost_model_for(row.asset_class)
    expected_entry_fill = model.buy_fill(row.close)
    stop = initial_stop(expected_entry_fill, row.atr14, config.portfolio.stop_atr)
    if stop <= 0:
        return None, "initial_stop_not_positive"
    risk_per_unit = model.long_risk_per_unit(expected_entry_fill, stop)
    if risk_per_unit <= 0:
        return None, "risk_per_unit_not_positive"
    remaining_risk = max(
        0.0,
        planning_equity * config.portfolio.max_open_risk_fraction - planning_open_risk,
    )
    plan = position_plan_for_risk(
        equity=planning_equity,
        entry=expected_entry_fill,
        stop=stop,
        risk_per_unit=risk_per_unit,
        risk_fraction=config.portfolio.risk_fraction,
        max_position_fraction=config.portfolio.max_position_fraction,
    )
    units_by_cash = max(0.0, planning_cash / model.buy_cash_per_unit(row.close))
    units_by_open_risk = remaining_risk / risk_per_unit
    units = min(plan.units, units_by_cash, units_by_open_risk)
    if not math.isfinite(units) or units <= 0:
        if remaining_risk <= 0:
            return None, "aggregate_open_risk_cap"
        if planning_cash <= 0:
            return None, "insufficient_paper_cash"
        return None, "no_eligible_units"

    ticket = PaperTicket(
        schema_version=OPERATIONS_SCHEMA_VERSION,
        ticket_id=_ticket_identity(observation, row, config),
        ticket_sha256="",
        archive_sha256=observation.archive_sha256,
        scanner_config_sha256=observation.scanner_config_sha256,
        operations_config_sha256=config.config_sha256,
        cost_config_sha256=config.cost_config_sha256,
        observation_date=observation.observation_date.isoformat(),
        signal_date=row.signal_date.isoformat(),
        symbol=row.symbol,
        asset_class=row.asset_class,
        score=row.score,
        planning_reference=row.close,
        expected_entry_fill=expected_entry_fill,
        atr14=row.atr14,
        initial_stop=stop,
        trailing_atr=config.portfolio.trail_atr,
        planned_units=units,
        planned_notional=units * expected_entry_fill,
        risk_per_unit=risk_per_unit,
        planned_initial_loss=units * risk_per_unit,
        planning_equity=planning_equity,
        planning_cash=planning_cash,
        planning_open_risk=planning_open_risk,
        currency=config.currency,
    )
    ticket = replace(ticket, ticket_sha256=_ticket_digest(ticket))
    _validate_ticket(ticket)
    return ticket, None


def build_daily_brief(
    archive_path: str | Path,
    config: PaperOperationsConfig,
    ledger_path: str | Path,
    *,
    archive_dir: str | Path | None = None,
) -> DailyBrief:
    """Create a deterministic paper-only brief from a verified scanner observation."""
    observation = load_daily_scan_observation(archive_path)
    state = load_paper_ledger(ledger_path, config)
    account = _account_state(state, observation, archive_dir, config)
    marked_by_symbol = {item.position.ticket.symbol for item in account.marked_positions}
    candidates: list[BriefCandidate] = []
    planning_cash = account.cash
    planning_open_risk = account.open_risk
    planning_position_count = len(account.marked_positions)

    for row in sorted(observation.rows, key=lambda item: (-item.score, item.symbol)):
        ticket_id = _ticket_identity(observation, row, config)
        existing_ticket = state.tickets.get(ticket_id)
        if existing_ticket is not None:
            decision = state.decisions[ticket_id]
            if ticket_id in state.closed_ticket_ids:
                status = "closed"
            elif row.symbol in marked_by_symbol:
                status = "open_position"
            elif decision == "approved":
                status = "approved_pending_entry"
            else:
                status = decision
            candidates.append(
                BriefCandidate(
                    symbol=row.symbol,
                    asset_class=row.asset_class,
                    score=row.score,
                    signal=row.signal,
                    signal_date=row.signal_date,
                    status=status,
                    reason="existing_human_ledger_event",
                    ticket=existing_ticket,
                )
            )
            continue
        if row.signal != "BUY":
            candidates.append(
                BriefCandidate(
                    symbol=row.symbol,
                    asset_class=row.asset_class,
                    score=row.score,
                    signal=row.signal,
                    signal_date=row.signal_date,
                    status="rejected",
                    reason="scanner_signal_is_not_buy",
                    ticket=None,
                )
            )
            continue
        if row.symbol in marked_by_symbol:
            candidates.append(
                BriefCandidate(
                    symbol=row.symbol,
                    asset_class=row.asset_class,
                    score=row.score,
                    signal=row.signal,
                    signal_date=row.signal_date,
                    status="rejected",
                    reason="already_open_paper_position",
                    ticket=None,
                )
            )
            continue
        if planning_position_count >= config.portfolio.max_positions:
            candidates.append(
                BriefCandidate(
                    symbol=row.symbol,
                    asset_class=row.asset_class,
                    score=row.score,
                    signal=row.signal,
                    signal_date=row.signal_date,
                    status="rejected",
                    reason="maximum_position_count",
                    ticket=None,
                )
            )
            continue
        ticket, reason = _new_ticket(
            observation,
            row,
            config,
            planning_equity=account.equity,
            planning_cash=planning_cash,
            planning_open_risk=planning_open_risk,
        )
        if ticket is None:
            candidates.append(
                BriefCandidate(
                    symbol=row.symbol,
                    asset_class=row.asset_class,
                    score=row.score,
                    signal=row.signal,
                    signal_date=row.signal_date,
                    status="rejected",
                    reason=reason,
                    ticket=None,
                )
            )
            continue
        candidates.append(
            BriefCandidate(
                symbol=row.symbol,
                asset_class=row.asset_class,
                score=row.score,
                signal=row.signal,
                signal_date=row.signal_date,
                status="eligible",
                reason=None,
                ticket=ticket,
            )
        )
        model = config.portfolio.cost_model_for(row.asset_class)
        planning_cash -= ticket.planned_units * model.buy_cash_per_unit(row.close)
        planning_open_risk += ticket.planned_initial_loss
        planning_position_count += 1

    return DailyBrief(
        observation=observation,
        config=config,
        account=account,
        candidates=tuple(candidates),
    )


def brief_as_dict(brief: DailyBrief) -> dict[str, Any]:
    """Return a JSON-safe projection suitable for CLI output and integration tests."""
    return {
        "schema_version": OPERATIONS_SCHEMA_VERSION,
        "mode": PAPER_MODE,
        "approval_required": True,
        "observation": {
            "archive": str(brief.observation.archive_path),
            "archive_sha256": brief.observation.archive_sha256,
            "observation_date": brief.observation.observation_date.isoformat(),
            "scanner_config_sha256": brief.observation.scanner_config_sha256,
            "recorder_code_sha": brief.observation.recorder_code_sha,
        },
        "account": {
            "currency": brief.config.currency,
            "cash": brief.account.cash,
            "equity": brief.account.equity,
            "open_risk": brief.account.open_risk,
            "open_position_count": len(brief.account.marked_positions),
        },
        "open_positions": [
            {
                "ticket_id": marked.position.ticket.ticket_id,
                "symbol": marked.position.ticket.symbol,
                "units": marked.position.units,
                "entry_date": marked.position.entry_date.isoformat(),
                "entry_reference": marked.position.entry_reference,
                "paper_entry_fill": marked.position.entry_fill,
                "initial_stop": marked.position.initial_stop,
                "current_trailing_stop": marked.current_stop,
                "highest_close_since_entry": marked.highest_close,
                "last_mark_date": (
                    None if marked.last_mark_date is None else marked.last_mark_date.isoformat()
                ),
                "trailing_rule": (
                    f"max(prior_stop, highest_close - {marked.position.ticket.trailing_atr:g} * ATR)"
                ),
            }
            for marked in brief.account.marked_positions
        ],
        "candidates": [
            {
                "symbol": candidate.symbol,
                "asset_class": candidate.asset_class,
                "score": candidate.score,
                "signal": candidate.signal,
                "signal_date": candidate.signal_date.isoformat(),
                "status": candidate.status,
                "reason": candidate.reason,
                "ticket": None if candidate.ticket is None else asdict(candidate.ticket),
            }
            for candidate in brief.candidates
        ],
        "boundaries": {
            "broker_orders_sent": False,
            "broker_credentials_used": False,
            "automatic_execution": False,
            "validation_evidence": False,
            "fill_guarantee": False,
            "entry_timing": ENTRY_TIMING,
        },
    }


def render_daily_brief(brief: DailyBrief) -> str:
    """Render a compact human-reviewable daily brief without presenting it as an order."""
    account = brief.account
    currency = brief.config.currency
    lines = [
        f"# Paper trading daily brief — {brief.observation.observation_date.isoformat()}",
        "",
        "Paper-only and approval-only. This tool sends no broker order and uses no broker credential.",
        "A planning reference is not a fill guarantee. Any paper entry must be recorded at a",
        "next available open after the completed signal date, then re-priced deterministically.",
        "",
        "## Account",
        "",
        f"- Cash: {account.cash:.2f} {currency}",
        f"- Marked equity: {account.equity:.2f} {currency}",
        f"- Open risk: {account.open_risk:.2f} {currency}",
        f"- Open positions: {len(account.marked_positions)}",
        "",
        "## Eligible long candidates",
        "",
    ]
    eligible = [candidate for candidate in brief.candidates if candidate.status == "eligible"]
    if eligible:
        lines.extend(
            [
                "| Ticket | Symbol | Score | Planning reference | Paper units | Initial stop | Planned loss |",
                "|---|---:|---:|---:|---:|---:|---:|",
            ]
        )
        for candidate in eligible:
            ticket = candidate.ticket
            assert ticket is not None
            lines.append(
                "| "
                f"{ticket.ticket_id} | {ticket.symbol} | {ticket.score} | "
                f"{ticket.planning_reference:.4f} | {ticket.planned_units:.6f} | "
                f"{ticket.initial_stop:.4f} | {ticket.planned_initial_loss:.2f} {currency} |"
            )
    else:
        lines.append("No new eligible long candidate.")

    lines.extend(("", "## Open paper positions", ""))
    if account.marked_positions:
        lines.extend(
            [
                "| Symbol | Units | Initial stop | Current trailing stop | Last completed mark |",
                "|---|---:|---:|---:|---:|",
            ]
        )
        for marked in account.marked_positions:
            last_mark = "not yet available" if marked.last_mark_date is None else marked.last_mark_date.isoformat()
            lines.append(
                "| "
                f"{marked.position.ticket.symbol} | {marked.position.units:.6f} | "
                f"{marked.position.initial_stop:.4f} | {marked.current_stop:.4f} | {last_mark} |"
            )
        lines.append("")
        lines.append(
            "Trailing rule: `max(prior stop, highest completed close - 2.5 × ATR)`; "
            "a stop is a market-reference trigger, not a guaranteed exit fill."
        )
    else:
        lines.append("No open paper position.")

    unavailable = [candidate for candidate in brief.candidates if candidate.status != "eligible"]
    lines.extend(("", "## Unavailable or already actioned", ""))
    if unavailable:
        lines.extend(["| Symbol | Score | Status | Reason |", "|---|---:|---|---|"])
        for candidate in unavailable:
            lines.append(
                f"| {candidate.symbol} | {candidate.score} | {candidate.status} | "
                f"{candidate.reason or 'n/a'} |"
            )
    else:
        lines.append("None.")

    lines.extend(
        (
            "",
            "## Boundary",
            "",
            "Paper records are operational evidence only. They cannot tune frozen v1 or satisfy "
            "the prospective-holdout validation gate.",
            "",
        )
    )
    return "\n".join(lines)
