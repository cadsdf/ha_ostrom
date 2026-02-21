"""Ostrom Electricity Consumption and Spot Price Visualization."""

from __future__ import annotations

import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from custom_components.ostrom.ostrom_data import OstromConsumerData


class OstromDataVisualizer:
    """Visualize received Ostrom electricity consumption and spot price data."""

    def __init__(self, data: OstromConsumerData) -> None:
        """Initialize parser with API response data."""
        self.data = data

    def plot_total_price(
        self, figsize: tuple[int, int] = (14, 8), save_path: str | None = None
    ) -> None:
        """Create a plot of total gross kWh prices over time."""
        if not self.data.spot_prices:
            print("No data to plot")
            return

        dates = [price.date for price in self.data.spot_prices]

        total_prices = [
            (price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh)
            * 100
            for price in self.data.spot_prices
        ]

        gross_prices = [
            price.price_gross_euro_per_kwh * 100 for price in self.data.spot_prices
        ]

        _, ax = plt.subplots(figsize=figsize)

        ax.fill_between(
            dates, 0, gross_prices, alpha=0.6, label="Energy Price", color="#3498db"
        )

        ax.fill_between(
            dates,
            gross_prices,
            total_prices,
            alpha=0.6,
            label="Taxes & Levies",
            color="#e74c3c",
        )

        ax.plot(
            dates,
            total_prices,
            linewidth=2,
            color="#2c3e50",
            label="Total Price",
            marker="o",
            markersize=4,
        )

        ax.set_xlabel("Time", fontsize=12, fontweight="bold")
        ax.set_ylabel("Price (ct/kWh)", fontsize=12, fontweight="bold")

        ax.set_title(
            "Hourly Energy Prices (Gross including Taxes)",
            fontsize=14,
            fontweight="bold",
        )

        ax.grid(True, alpha=0.3, linestyle="--")
        ax.legend(loc="upper left", fontsize=10)

        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.xticks(rotation=45, ha="right")

        avg_price = sum(total_prices) / len(total_prices)
        min_price = min(total_prices)
        max_price = max(total_prices)
        min_time = dates[total_prices.index(min_price)].strftime("%H:%M")
        max_time = dates[total_prices.index(max_price)].strftime("%H:%M")

        stats_text = f"Average: {avg_price:.2f} ct/kWh\n"
        stats_text += f"Min: {min_price:.2f} ct/kWh at {min_time}\n"
        stats_text += f"Max: {max_price:.2f} ct/kWh at {max_time}"

        ax.text(
            0.98,
            0.97,
            stats_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
            horizontalalignment="right",
            bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.8},
        )

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Plot saved to {save_path}")

        plt.show()

    def plot_price_breakdown(
        self, figsize: tuple[int, int] = (14, 8), save_path: str | None = None
    ) -> None:
        """Create a detailed breakdown plot of price components."""
        if not self.data.spot_prices:
            print("No data to plot")
            return

        dates = [price.date for price in self.data.spot_prices]
        net_prices = [
            price.price_net_euro_per_kwh * 100 for price in self.data.spot_prices
        ]
        gross_prices = [
            price.price_gross_euro_per_kwh * 100 for price in self.data.spot_prices
        ]
        taxes = [
            price.tax_and_levies_gross_euro_per_kwh * 100
            for price in self.data.spot_prices
        ]
        total_prices = [
            (price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh)
            * 100
            for price in self.data.spot_prices
        ]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

        ax1.plot(
            dates,
            net_prices,
            label="Net kWh Price",
            linewidth=2,
            marker="o",
            markersize=3,
        )
        ax1.plot(
            dates,
            gross_prices,
            label="Gross kWh Price",
            linewidth=2,
            marker="s",
            markersize=3,
        )
        ax1.plot(
            dates,
            total_prices,
            label="Total (incl. Taxes)",
            linewidth=2.5,
            marker="D",
            markersize=3,
            color="#e74c3c",
        )

        ax1.set_ylabel("Price (ct/kWh)", fontsize=11, fontweight="bold")

        ax1.set_title(
            "Energy Price Components Over Time", fontsize=13, fontweight="bold"
        )

        ax1.grid(True, alpha=0.3, linestyle="--")
        ax1.legend(loc="upper left", fontsize=9)

        ax2.fill_between(
            dates, taxes, alpha=0.7, label="Taxes & Levies", color="#e67e22"
        )
        ax2.plot(dates, taxes, linewidth=2, color="#d35400")
        ax2.set_xlabel("Time", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Taxes (ct/kWh)", fontsize=11, fontweight="bold")
        ax2.set_title("Taxes and Levies", fontsize=13, fontweight="bold")
        ax2.grid(True, alpha=0.3, linestyle="--")
        ax2.legend(loc="upper left", fontsize=9)

        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.xticks(rotation=45, ha="right")

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Plot saved to {save_path}")

        plt.show()

    def print_summary(self) -> None:
        """Print a summary of the energy price data."""
        if not self.data.spot_prices:
            print("No data available")
            return

        total_prices = [
            (price.price_gross_euro_per_kwh + price.tax_and_levies_gross_euro_per_kwh)
            * 100
            for price in self.data.spot_prices
        ]
        avg_price = sum(total_prices) / len(total_prices)
        min_price = min(total_prices)
        max_price = max(total_prices)

        min_idx = total_prices.index(min_price)
        max_idx = total_prices.index(max_price)

        print("\n" + "=" * 60)
        print("ELECTRICITY PRICE SUMMARY")
        print("=" * 60)
        print(
            f"Period: {self.data.spot_prices[0].date.strftime('%Y-%m-%d %H:%M')} to {self.data.spot_prices[-1].date.strftime('%Y-%m-%d %H:%M')}"
        )
        print(f"Number of data points: {len(self.data.spot_prices)}")
        print(f"\nAverage total price: {avg_price:.2f} ct/kWh")
        print(
            f"Minimum price: {min_price:.2f} ct/kWh at {self.data.spot_prices[min_idx].date.strftime('%H:%M')}"
        )
        print(
            f"Maximum price: {max_price:.2f} ct/kWh at {self.data.spot_prices[max_idx].date.strftime('%H:%M')}"
        )
        print(f"Price range: {max_price - min_price:.2f} ct/kWh")
        print(
            f"\nAverage energy price: {sum(p.price_gross_euro_per_kwh * 100 for p in self.data.spot_prices) / len(self.data.spot_prices):.2f} ct/kWh"
        )
        print(
            f"Average taxes/levies: {sum(p.tax_and_levies_gross_euro_per_kwh * 100 for p in self.data.spot_prices) / len(self.data.spot_prices):.2f} ct/kWh"
        )
        print("=" * 60 + "\n")
