#!/usr/bin/env python3
"""
Ostrom API Client
Handles OAuth2 authentication and API requests for Ostrom sandbox API
"""

import argparse
import asyncio
import os
import sys

import matplotlib.pyplot as plt

from custom_components.ostrom.ostrom_data import OstromConsumerData
from custom_components.ostrom.ostrom_error import OstromError
from custom_components.ostrom.ostrom_provider import OstromProvider
from ostrom_visualization import OstromDataVisualizer


async def run_async(provider: OstromProvider, visualize: bool = False) -> int:
    """Run the main async loop to fetch data and optionally visualize"""

    # Initialize provider, get access token, fetch user and contracts
    error = await provider.initialize()

    if error is not None:
        print(f"Initialization error: {error}", file=sys.stderr, flush=True)
        return error.error_code if hasattr(error, "error_code") else 1

    # Update all data
    ret: str | OstromError | None = await provider.update_data()

    if isinstance(ret, OstromError):
        print(f"Error: {ret}", file=sys.stderr, flush=True)
        return ret.error_code if hasattr(ret, "error_code") else 1

    elif ret is not None:
        print(f"{ret}", flush=True)

    # Visualize if requested
    if visualize:
        data: OstromConsumerData | None = provider.get_consumer_data()

        if not data or not data.consumptions:
            print("Warning: No consumption data to visualize", file=sys.stderr)
            return 1

        if not data.spot_prices:
            print("Warning: No spot price data to visualize", file=sys.stderr)
            return 1

        visualizer = OstromDataVisualizer(data)
        visualizer.print_summary()
        visualizer.plot_total_price(figsize=(14, 8), save_path=None)
        visualizer.plot_price_breakdown(figsize=(14, 8), save_path=None)

        # Keep plots open until user closes them
        plt.show(block=True)

    return 0


def main():
    """Main entry point with command-line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Ostrom API Client - Fetch and visualize energy consumption and spot price data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use environment variables for credentials
  %(prog)s --visualize

  # Provide credentials via command line
  %(prog)s --user CLIENT_ID --secret CLIENT_SECRET --zip 12345 --visualize
        """,
    )

    # Credentials
    parser.add_argument(
        "--user",
        "-u",
        type=str,
        help="Client ID (alternative to OSTROM_CLIENT_ID env var)",
    )

    parser.add_argument(
        "--secret",
        "-s",
        type=str,
        help="Client secret (alternative to OSTROM_CLIENT_SECRET env var)",
    )

    parser.add_argument(
        "--zip",
        "-z",
        type=str,
        help="ZIP code for spot price data (alternative to OSTROM_CLIENT_ZIP env var)",
    )

    # API endpoints
    parser.add_argument(
        "--endpoint-auth",
        type=str,
        help="Authentication endpoint URL (alternative to OSTROM_API_ENDPOINT_AUTH env var)",
    )

    parser.add_argument(
        "--endpoint-data",
        type=str,
        help="Data endpoint URL (alternative to OSTROM_API_ENDPOINT_DATA env var)",
    )

    # Visualization
    parser.add_argument(
        "--visualize",
        "-v",
        action="store_true",
        help="Enable data visualization with plots",
    )

    args = parser.parse_args()

    # Load credentials from command line arguments or environment variables
    client_id: str | None = args.user or os.getenv("OSTROM_CLIENT_ID")
    client_secret: str | None = args.secret or os.getenv("OSTROM_CLIENT_SECRET")
    client_zip: str | None = args.zip or os.getenv("OSTROM_CLIENT_ZIP")

    endpoint_auth: str | None = args.endpoint_auth or os.getenv(
        "OSTROM_API_ENDPOINT_AUTH"
    )

    endpoint_data: str | None = args.endpoint_data or os.getenv(
        "OSTROM_API_ENDPOINT_DATA"
    )

    if not client_id or not client_secret:
        print("Error: Client ID and secret must be provided", file=sys.stderr)
        print("\nProvide credentials via command line arguments:")
        print("  --user CLIENT_ID --secret CLIENT_SECRET")
        print("\nOr set environment variables:")
        print("  export OSTROM_CLIENT_ID='your_client_id'")
        print("  export OSTROM_CLIENT_SECRET='your_client_secret'")
        return 1

    if not client_zip:
        print("Warning: ZIP code not provided, spot price data will not be fetched")

    # Create provider
    provider: OstromProvider = OstromProvider(
        user=client_id,
        password=client_secret,
        endpoint_auth=endpoint_auth,
        endpoint_data=endpoint_data,
        zip_code=client_zip,
        contract_id=None,
    )

    # Run async main loop
    return asyncio.run(run_async(provider, visualize=args.visualize))


if __name__ == "__main__":
    exit(main())
