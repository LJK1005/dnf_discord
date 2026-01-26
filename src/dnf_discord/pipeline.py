import logging
from typing import Dict, List

from .config import load_accounts, load_settings
from .discord_client import DiscordBot
from .logging_setup import setup_logging
from .scraper import build_driver, scrape_character_stats
from .storage_mongo import MongoStorage


def run() -> None:
    settings = load_settings()
    log_file = setup_logging(settings.log_dir)
    logger = logging.getLogger(__name__)
    logger.info("Logging to %s", log_file)
    accounts = load_accounts(settings.accounts_path)
    logger.info("Loaded %d accounts from %s", len(accounts), settings.accounts_path)

    storage = MongoStorage(settings.mongo_uri, settings.mongo_db)
    logger.info("MongoDB client initialized for %s/%s", settings.mongo_uri, settings.mongo_db)

    driver = build_driver(settings.chromedriver_path)
    try:
        logger.info("Starting scrape and update phase")
        _scrape_and_update(driver, storage, accounts)
        logger.info("Completed scrape and update phase")
    except Exception:
        logger.exception("Scrape and update phase failed")
        raise
    finally:
        driver.quit()
        logger.info("Selenium driver closed")

    bot = DiscordBot(
        token=settings.discord_token,
        channel_id=settings.discord_channel_id,
        storage=storage,
        accounts=accounts,
        tmp_dir=settings.tmp_dir,
    )
    logger.info("Starting Discord bot run")
    bot.run_bot()
    logger.info("Discord bot run completed")

    storage.close()
    logger.info("MongoDB client closed")


def _scrape_and_update(
    driver,
    storage: MongoStorage,
    accounts: Dict[str, List[str]],
) -> None:
    logger = logging.getLogger(__name__)
    for account_name, nicknames in accounts.items():
        logger.info("Scraping account=%s nicknames=%d", account_name, len(nicknames))
        for nickname in nicknames:
            logger.info("Scraping nickname=%s", nickname)
            try:
                stats = scrape_character_stats(driver, account_name, nickname)
            except Exception:
                logger.exception(
                    "Scrape failed for account=%s nickname=%s", account_name, nickname
                )
                continue

            if not stats:
                logger.warning(
                    "No stats found for account=%s nickname=%s", account_name, nickname
                )
                continue

            logger.info(
                "Stats scraped for account=%s nickname=%s keys=%s",
                account_name,
                nickname,
                ", ".join(sorted(stats.keys())),
            )
            storage.upsert_stats(account_name, nickname, stats)
            logger.info(
                "Mongo upsert complete for account=%s nickname=%s",
                account_name,
                nickname,
            )
