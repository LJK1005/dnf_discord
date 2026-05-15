from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Union

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ACCOUNTS_PATH = PROJECT_ROOT / "config" / "accounts.json"
DEFAULT_TMP_DIR = PROJECT_ROOT / "tmp"
DEFAULT_LOG_DIR = PROJECT_ROOT / "logs"


@dataclass(frozen=True)
class Settings:
    mongo_uri: str
    mongo_db: str
    discord_token: str
    discord_channel_id: int
    discord_app_id: Optional[str]
    discord_public_key: Optional[str]
    chromedriver_path: str
    accounts_path: Path
    tmp_dir: Path
    log_dir: Path


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _resolve_path(value: Union[str, Path]) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        return PROJECT_ROOT / path
    return path


def load_settings(env_path: Optional[Path] = None) -> Settings:
    if env_path is None:
        env_path = PROJECT_ROOT / ".env"

    load_dotenv(env_path)

    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    mongo_db = os.getenv("MONGO_DB", "dnf_discord")

    discord_token = _require_env("DISCORD_TOKEN")
    discord_channel_id = int(_require_env("DISCORD_CHANNEL_ID"))
    discord_app_id = os.getenv("DISCORD_APP_ID")
    discord_public_key = os.getenv("DISCORD_PUBLIC_KEY")

    chromedriver_path = _require_env("CHROMEDRIVER_PATH")

    accounts_path = _resolve_path(os.getenv("ACCOUNTS_PATH", DEFAULT_ACCOUNTS_PATH))
    tmp_dir = _resolve_path(os.getenv("TMP_DIR", DEFAULT_TMP_DIR))
    tmp_dir.mkdir(parents=True, exist_ok=True)
    log_dir = _resolve_path(os.getenv("LOG_DIR", DEFAULT_LOG_DIR))
    log_dir.mkdir(parents=True, exist_ok=True)

    return Settings(
        mongo_uri=mongo_uri,
        mongo_db=mongo_db,
        discord_token=discord_token,
        discord_channel_id=discord_channel_id,
        discord_app_id=discord_app_id,
        discord_public_key=discord_public_key,
        chromedriver_path=chromedriver_path,
        accounts_path=accounts_path,
        tmp_dir=tmp_dir,
        log_dir=log_dir,
    )


def load_accounts(path: Path) -> Dict[str, List[str]]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError("accounts.json must be an object of account -> nicknames")

    accounts: Dict[str, List[str]] = {}
    for account, nicknames in data.items():
        if not isinstance(account, str):
            raise ValueError("Account name must be a string")
        if not isinstance(nicknames, list) or not all(isinstance(n, str) for n in nicknames):
            raise ValueError(f"Nicknames for {account} must be a list of strings")
        accounts[account] = nicknames

    return accounts
