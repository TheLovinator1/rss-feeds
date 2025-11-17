"""Backfill AMD keys availability CSV from git history of amd_response.json.

This script walks the git history for pages/data/amd_response.json, extracts
keysAvailable per promotion at each commit, and appends rows to
pages/data/amd_gaming_keys_available.csv using the commit timestamp.

Usage:
    uv run python amd/backfill_from_git.py

Notes:
- Uses commit author timestamp (UTC) for the `timestamp` column
- Skips commits where the file doesn't exist or JSON is invalid
- Avoids writing duplicate (timestamp, promotion_id) rows already in CSV
"""

from __future__ import annotations

import csv
import json
import shutil
import subprocess  # noqa: S404 - controlled git CLI usage
from dataclasses import dataclass
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import Any
from typing import cast

from loguru import logger

REPO_ROOT: Path = Path(__file__).resolve().parent.parent
JSON_REL_PATH = Path("pages/data/amd_response.json")
CSV_REL_PATH = Path("pages/data/amd_gaming_keys_available.csv")


@dataclass(frozen=True)
class CsvRow:
    timestamp: str
    promotion_id: str | None
    title: str | None
    slug: str | None
    keys_available: int | None
    status: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "promotion_id": self.promotion_id,
            "title": self.title,
            "slug": self.slug,
            "keys_available": self.keys_available,
            "status": self.status,
        }


def run_git_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    """Run a git command and return the completed process.

    Args:
        args: Arguments to pass to the git executable (without the executable itself).

    Returns:
        The completed process with stdout/stderr captured as text.

    Raises:
        RuntimeError: If the git executable cannot be located on PATH.
    """
    git_exe: str | None = shutil.which("git")
    if not git_exe:
        msg = "git executable not found on PATH"
        raise RuntimeError(msg)

    return subprocess.run(  # noqa: S603 - arguments are static and executable is resolved
        [git_exe, *args],
        cwd=REPO_ROOT,
        text=True,
        check=True,
        capture_output=True,
    )


def get_commit_history_for_file(rel_path: Path) -> list[tuple[str, int]]:
    """Return list of (sha, author_unix_ts) for commits touching rel_path."""
    try:
        result: subprocess.CompletedProcess[str] = run_git_command([
            "--no-pager",
            "log",
            "--follow",
            "--format=%H|%ct",
            str(rel_path.as_posix()),
        ])
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get git log: {e.stderr}")
        return []

    commits: list[tuple[str, int]] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        try:
            sha, ts = line.split("|", 1)
            commits.append((sha, int(ts)))
        except ValueError:
            logger.warning(f"Skipping malformed log line: {line}")
            continue

    # Oldest to newest for chronological appends
    commits.reverse()
    return commits


def get_file_at_commit(sha: str, rel_path: Path) -> str | None:
    """Return file content at commit sha for rel_path, or None if missing."""
    try:
        result: subprocess.CompletedProcess[str] = run_git_command(["show", f"{sha}:{rel_path.as_posix()}"])
    except subprocess.CalledProcessError:
        # File may not exist at this commit
        return None
    else:
        return result.stdout


def parse_rows_from_json(json_text: str, commit_ts: int) -> list[CsvRow]:
    """Parse JSON content into CsvRow list using the given commit timestamp.

    Args:
        json_text: The JSON string to parse (expected amd_response.json format).
        commit_ts: Commit author timestamp (seconds since epoch, UTC).

    Returns:
        A list of CsvRow entries extracted from the JSON at that commit.
    """
    try:
        parsed: Any = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.warning(f"Skipping commit due to JSON parse error: {e}")
        return []

    iso_ts: str = datetime.fromtimestamp(commit_ts, UTC).isoformat()

    if not isinstance(parsed, dict):
        return []

    data: dict[str, Any] = cast("dict[str, Any]", parsed)
    items_obj: Any = data.get("items", [])
    if not isinstance(items_obj, list):
        return []

    items_list: list[dict[str, Any]] = cast("list[dict[str, Any]]", items_obj)

    rows: list[CsvRow] = []
    for item in items_list:
        promotion_id: str | None = item.get("id")
        title: str | None = item.get("title")
        slug: str | None = item.get("slug")
        keys_available: int | None = item.get("keysAvailable")
        status: str | None = item.get("status")

        rows.append(
            CsvRow(
                timestamp=iso_ts,
                promotion_id=str(promotion_id) if promotion_id is not None else None,
                title=str(title) if title is not None else None,
                slug=str(slug) if slug is not None else None,
                keys_available=int(keys_available) if isinstance(keys_available, int) else None,
                status=str(status) if status is not None else None,
            ),
        )
    return rows


def read_existing_pairs(csv_path: Path) -> set[tuple[str, str]]:
    """Read existing (timestamp, promotion_id) pairs to avoid duplicates.

    Args:
        csv_path: Path to the existing CSV file if present.

    Returns:
        A set of (timestamp, promotion_id) tuples already present in the CSV.
    """
    pairs: set[tuple[str, str]] = set()
    if not csv_path.exists():
        return pairs

    with csv_path.open(encoding="utf-8") as f:
        reader: csv.DictReader[str] = csv.DictReader(f)
        for row in reader:
            ts: str | None = row.get("timestamp")
            pid: str | None = row.get("promotion_id")
            if ts and pid:
                pairs.add((ts, pid))
    return pairs


def append_rows(csv_path: Path, rows: list[CsvRow]) -> int:
    """Append rows to CSV, writing header if needed.

    Args:
        csv_path: Path to the CSV file to append to.
        rows: Rows to write.

    Returns:
        The number of rows successfully written.
    """
    if not rows:
        return 0

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    exists: bool = csv_path.exists()

    with csv_path.open("a", newline="", encoding="utf-8") as f:
        fieldnames: list[str] = ["timestamp", "promotion_id", "title", "slug", "keys_available", "status"]
        writer: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r.as_dict())
    return len(rows)


def main() -> None:
    """Backfill the keys availability CSV using git history snapshots."""
    logger.info("Starting backfill from git history")

    rel_json: Path = JSON_REL_PATH
    rel_csv: Path = CSV_REL_PATH

    commits: list[tuple[str, int]] = get_commit_history_for_file(rel_json)
    logger.info(f"Found {len(commits)} commits touching {rel_json}")

    existing_pairs: set[tuple[str, str]] = read_existing_pairs(REPO_ROOT / rel_csv)
    logger.info(f"Loaded {len(existing_pairs)} existing (timestamp,promotion_id) pairs")

    new_rows: list[CsvRow] = []

    for sha, ts in commits:
        content: str | None = get_file_at_commit(sha, rel_json)
        if content is None:
            continue
        rows: list[CsvRow] = parse_rows_from_json(content, ts)
        for r in rows:
            key: tuple[str, str] = (r.timestamp, r.promotion_id or "")
            if key in existing_pairs:
                continue
            new_rows.append(r)
            existing_pairs.add(key)

    # Sort rows by timestamp ascending for stable CSV
    new_rows.sort(key=lambda r: r.timestamp)

    written: int = append_rows(REPO_ROOT / rel_csv, new_rows)
    logger.success(f"Backfill complete. Appended {written} rows to {rel_csv}")


if __name__ == "__main__":
    main()
