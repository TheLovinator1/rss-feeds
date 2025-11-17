"""CSV logger for tracking AMD Gaming promotion key availability over time."""

import csv
import json
from datetime import UTC
from datetime import datetime
from pathlib import Path

from loguru import logger


def append_keys_data_to_csv(json_path: Path, csv_path: Path) -> None:
    """Append current keysAvailable data to CSV file.

    Args:
        json_path: Path to the amd_response.json file
        csv_path: Path to the keys_available.csv file
    """
    # Read JSON data
    with json_path.open(encoding="utf-8") as f:
        data: dict[str, list[dict[str, str]]] = json.load(f)

    # Get current timestamp
    timestamp: str = datetime.now(UTC).isoformat()

    # Prepare rows to append
    rows: list[dict[str, str | None]] = [
        {
            "timestamp": timestamp,
            "promotion_id": item.get("id"),
            "title": item.get("title"),
            "slug": item.get("slug"),
            "keys_available": item.get("keysAvailable"),
            "status": item.get("status"),
        }
        for item in data.get("items", [])
    ]

    # Check if CSV exists
    csv_exists: bool = csv_path.exists()

    # Append to CSV
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        fieldnames: list[str] = ["timestamp", "promotion_id", "title", "slug", "keys_available", "status"]
        writer: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=fieldnames)

        # Write header if file doesn't exist
        if not csv_exists:
            writer.writeheader()

        writer.writerows(rows)


if __name__ == "__main__":
    # Default paths
    json_path: Path = Path(__file__).parent.parent / "pages" / "data" / "amd_response.json"
    csv_path: Path = Path(__file__).parent.parent / "pages" / "data" / "amd_gaming_keys_available.csv"

    append_keys_data_to_csv(json_path, csv_path)
    logger.info(f"Appended keys data to {csv_path}")
