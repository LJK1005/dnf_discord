import argparse
import csv
import os
from pathlib import Path
from typing import Dict, Optional

from dotenv import load_dotenv

from .config import DEFAULT_ACCOUNTS_PATH, PROJECT_ROOT, load_accounts
from .parser import parse_korean_number
from .scraper import STAT_NAME_MAP
from .storage_mongo import MongoStorage


NICKNAME_COLUMN = "닉네임"


def _resolve_path(path: Path) -> Path:
    if path.is_absolute():
        return path
    return PROJECT_ROOT / path


def _to_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None

    text = text.replace(",", "")
    if text.endswith(".0"):
        text = text[:-2]

    if not text:
        return None

    try:
        return int(text)
    except ValueError:
        korean = parse_korean_number(text)
        if korean != 0:
            return korean
        try:
            return int(float(text))
        except ValueError:
            return None


def _extract_stats(row: Dict[str, str]) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    for column, raw_value in row.items():
        if column == NICKNAME_COLUMN:
            continue
        key = STAT_NAME_MAP.get(column.strip())
        if not key:
            continue
        value = _to_int(raw_value)
        if value is None:
            continue
        stats[key] = value
    return stats


def _migrate_csv_file(account_name: str, csv_path: Path, storage: MongoStorage) -> int:
    count = 0
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            nickname = row.get(NICKNAME_COLUMN)
            if not nickname:
                continue
            stats = _extract_stats(row)
            storage.upsert_stats(account_name, nickname, stats)
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="One-time CSV to MongoDB migration for DNF data."
    )
    parser.add_argument(
        "--csv-dir",
        default=str(PROJECT_ROOT),
        help="Directory containing account CSV files (default: project root).",
    )
    parser.add_argument(
        "--accounts-path",
        default=str(DEFAULT_ACCOUNTS_PATH),
        help="Path to accounts.json (default: config/accounts.json).",
    )
    parser.add_argument(
        "--env-path",
        default=str(PROJECT_ROOT / ".env"),
        help="Path to .env for Mongo settings (default: .env).",
    )
    args = parser.parse_args()

    csv_dir = _resolve_path(Path(args.csv_dir))
    accounts_path = _resolve_path(Path(args.accounts_path))
    env_path = _resolve_path(Path(args.env_path))

    if env_path.exists():
        load_dotenv(env_path)

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "dnf_discord")

    accounts = load_accounts(accounts_path)

    storage = MongoStorage(mongo_uri, mongo_db)
    try:
        for account_name in accounts.keys():
            csv_path = csv_dir / f"{account_name}.csv"
            if not csv_path.exists():
                print(f"CSV not found: {csv_path}")
                continue
            count = _migrate_csv_file(account_name, csv_path, storage)
            print(f"Imported {count} rows for {account_name}")
    finally:
        storage.close()


if __name__ == "__main__":
    main()
