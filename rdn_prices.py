"""CLI entry point for fetching and plotting RDN energy prices."""
from __future__ import annotations

import argparse
import os
import sys

from rdn_data import DEFAULT_PSE_URL, fetch_pse_prices, normalize_prices, resolve_date_range
from rdn_plot import plot_prices


def build_parser() -> argparse.ArgumentParser:
    """Expose a minimal CLI so the script is easy to reuse."""

    parser = argparse.ArgumentParser(
        description=(
            "Pobiera historyczne ceny RDN z API PSE i generuje wykres liniowy."
        )
    )
    parser.add_argument(
        "--days",
        type=int,
        default=int(os.getenv("RDN_DAYS", "30")),
        help="Liczba dni historii do pobrania (domyślnie 30).",
    )
    parser.add_argument(
        "--output",
        default=os.getenv("RDN_OUTPUT", "rdn_prices.png"),
        help="Ścieżka zapisu wykresu (domyślnie rdn_prices.png).",
    )
    parser.add_argument(
        "--pse-url",
        default=DEFAULT_PSE_URL,
        help="Adres API PSE (można nadpisać przez PSE_DAM_URL).",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Wyświetl wykres w oknie interaktywnym.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        date_range = resolve_date_range(args.days)
        raw_df = fetch_pse_prices(date_range, base_url=args.pse_url)
        prices = normalize_prices(raw_df, date_range)
        average = plot_prices(prices, args.output, show=args.show)
    except Exception as exc:  # noqa: BLE001 - user-facing error handling
        print(f"Błąd podczas pobierania lub przetwarzania danych: {exc}", file=sys.stderr)
        sys.exit(1)

    print(
        "Gotowe! Wykres zapisano w pliku: "
        f"{args.output}. Średnia cena: {average:.2f} PLN/MWh."
    )


if __name__ == "__main__":
    main()
