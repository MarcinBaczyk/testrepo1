"""Utilities for fetching and normalizing RDN price data."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import io
import os
from typing import Iterable, Optional

import pandas as pd
import requests

DEFAULT_PSE_URL = os.getenv("PSE_DAM_URL", "https://api.pse.pl/api/market-data/price-dam")
DEFAULT_TIMEOUT = 30


@dataclass(frozen=True)
class DateRange:
    """Date span used to request a consistent time window."""

    start: date
    end: date


def resolve_date_range(days: int) -> DateRange:
    """Derive a rolling date range so the chart stays current."""

    if days <= 0:
        raise ValueError("Number of days must be greater than zero.")
    end_date = date.today()
    start_date = end_date - timedelta(days=days)
    return DateRange(start=start_date, end=end_date)


def fetch_pse_prices(date_range: DateRange, base_url: str = DEFAULT_PSE_URL) -> pd.DataFrame:
    """Fetch raw PSE data, handling both JSON and CSV formats."""

    params = {
        "dateFrom": date_range.start.isoformat(),
        "dateTo": date_range.end.isoformat(),
    }
    try:
        response = requests.get(base_url, params=params, timeout=DEFAULT_TIMEOUT)
    except requests.exceptions.ConnectionError as exc:
        raise ValueError(_build_connection_hint(base_url)) from exc
    if response.status_code == 404:
        raise ValueError(_build_not_found_hint(base_url, date_range))
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "json" in content_type.lower():
        payload = response.json()
        records = _extract_records(payload)
        return pd.DataFrame(records)

    return pd.read_csv(io.StringIO(response.text), sep=";", engine="python")


def normalize_prices(raw_df: pd.DataFrame, date_range: DateRange) -> pd.DataFrame:
    """Normalize columns so downstream logic can stay consistent."""

    if raw_df.empty:
        raise ValueError("No data returned from the source.")

    date_col = _find_column(raw_df.columns, ("data", "date"))
    hour_col = _find_column(raw_df.columns, ("godzina", "hour"))
    price_col = _find_column(raw_df.columns, ("cena", "price"))

    if not date_col or not price_col:
        raise ValueError("Could not locate required date/price columns in the dataset.")

    timestamp = _build_timestamp(raw_df, date_col, hour_col)
    price = _parse_price(raw_df[price_col])

    normalized = pd.DataFrame({"timestamp": timestamp, "price": price}).dropna()
    normalized = normalized.sort_values("timestamp").reset_index(drop=True)

    mask = (normalized["timestamp"].dt.date >= date_range.start) & (
        normalized["timestamp"].dt.date <= date_range.end
    )
    filtered = normalized.loc[mask]
    if filtered.empty:
        raise ValueError("No valid price data found for the selected date range.")

    return filtered


def _extract_records(payload: object) -> Iterable[dict]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("data", "values", "records", "result"):
            if key in payload and isinstance(payload[key], list):
                return payload[key]
    raise ValueError("Unexpected JSON format returned from PSE API.")


def _build_not_found_hint(base_url: str, date_range: DateRange) -> str:
    if "/getcsv/" in base_url:
        return (
            "PSE zwróciło błąd 404 dla legacy endpointu CSV. Ten adres został "
            "wycofany lub zakres dat jest niedostępny (np. obejmuje przyszłość). "
            "Użyj oficjalnego API https://api.pse.pl/api/market-data/price-dam "
            "albo wybierz dostępny zakres danych."
        )
    return (
        "PSE API zwróciło błąd 404. Sprawdź, czy podany zakres dat "
        f"({date_range.start.isoformat()} - {date_range.end.isoformat()}) "
        "jest dostępny oraz czy używany jest poprawny endpoint."
    )


def _build_connection_hint(base_url: str) -> str:
    return (
        "Nie udało się nawiązać połączenia z API PSE (problem z DNS lub siecią). "
        "Sprawdź połączenie internetowe, ustawienia DNS/VPN/firewalla "
        "oraz czy host jest osiągalny. Używany endpoint: "
        f"{base_url}."
    )


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> Optional[str]:
    lowered = {col: col.lower() for col in columns}
    for col, lowered_col in lowered.items():
        for candidate in candidates:
            if candidate in lowered_col:
                return col
    return None


def _build_timestamp(df: pd.DataFrame, date_col: str, hour_col: Optional[str]) -> pd.Series:
    date_series = pd.to_datetime(df[date_col], errors="coerce", dayfirst=True)
    if hour_col:
        hour_series = pd.to_numeric(df[hour_col], errors="coerce")
        if hour_series.notna().any():
            hour_series = hour_series.fillna(1) - 1
            return date_series + pd.to_timedelta(hour_series, unit="h")
    return date_series


def _parse_price(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace("\u00a0", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    return pd.to_numeric(cleaned, errors="coerce")
