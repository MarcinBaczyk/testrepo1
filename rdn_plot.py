"""Plotting utilities for RDN price data."""
from __future__ import annotations

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd


def plot_prices(
    prices: pd.DataFrame,
    output_path: str,
    *,
    days: int | None = None,
    show: bool = False,
) -> float:
    """Render the line chart and return the average price for reporting."""

    sns.set_theme(style="whitegrid")
    fig, ax = plt.subplots(figsize=(12, 6))

    ax.plot(prices["timestamp"], prices["price"], label="Cena RDN", color="#1f77b4")
    average_price = prices["price"].mean()
    ax.axhline(
        average_price,
        color="#d62728",
        linestyle="--",
        linewidth=1.5,
        label=f"Średnia: {average_price:.2f} PLN/MWh",
    )

    if days:
        ax.set_title(f"RDN - ceny energii elektrycznej (ostatnie {days} dni)")
    else:
        ax.set_title("RDN - ceny energii elektrycznej (ostatni okres)")
    ax.set_xlabel("Data")
    ax.set_ylabel("Cena [PLN/MWh]")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend()

    fig.tight_layout()
    fig.savefig(output_path, dpi=150)

    if show:
        plt.show()
    else:
        plt.close(fig)

    return average_price
