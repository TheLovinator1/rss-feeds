"""Example script for visualizing key availability data from CSV.

Requirements:
    pip install pandas matplotlib

Usage:
    python amd/visualize_keys.py
"""
# ruff: noqa: T201

import csv
from datetime import datetime
from pathlib import Path


def print_summary() -> None:
    """Print summary statistics of key availability."""
    csv_path = Path(__file__).parent.parent / "pages" / "data" / "amd_gaming_keys_available.csv"

    if not csv_path.exists():
        print(f"CSV file not found: {csv_path}")
        return

    with csv_path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("No data in CSV file")
        return

    print(f"\n📊 Key Availability Summary ({len(rows)} records)\n")
    print("=" * 80)

    # Group by promotion
    promotions: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        promo_id = row["promotion_id"]
        if promo_id not in promotions:
            promotions[promo_id] = []
        promotions[promo_id].append(row)

    # Print stats for each promotion
    for records in promotions.values():
        title = records[0]["title"]
        slug = records[0]["slug"]

        # Get key availability over time
        timestamps = [datetime.fromisoformat(r["timestamp"]) for r in records]
        keys = [int(r["keys_available"]) for r in records]

        print(f"\n🎮 {title}")
        print(f"   Slug: {slug}")
        print(f"   Records: {len(records)}")
        print(f"   Latest keys available: {keys[-1]:,}")

        if len(keys) > 1:
            key_change = keys[-1] - keys[0]
            print(f"   Change since first record: {key_change:+,}")

            # Show timeline if we have multiple records
            print("\n   Timeline:")
            for ts, key_count in zip(timestamps[-5:], keys[-5:], strict=False):  # Show last 5 records
                print(f"   • {ts.strftime('%Y-%m-%d %H:%M')} UTC: {key_count:,} keys")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    print_summary()

    print("\n💡 To create graphs, install pandas and matplotlib:")
    print("   uv add pandas matplotlib")
    print("\nExample code for creating a line chart:")
    print("""
    import pandas as pd
    import matplotlib.pyplot as plt

    # Load data
    df = pd.read_csv('pages/data/amd_gaming_keys_available.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Plot for each promotion
    for promo_id in df['promotion_id'].unique():
        promo_data = df[df['promotion_id'] == promo_id]
        plt.plot(promo_data['timestamp'], promo_data['keys_available'],
                 marker='o', label=promo_data['title'].iloc[0])

    plt.xlabel('Date')
    plt.ylabel('Keys Available')
    plt.title('AMD Gaming Promotions - Key Availability Over Time')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig('keys_availability.png')
    plt.show()
    """)
