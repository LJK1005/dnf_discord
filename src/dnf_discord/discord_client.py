import asyncio
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Union

import dataframe_image
import discord
from discord.ext import commands
import pandas as pd

from .parser import format_korean_number
from .storage_mongo import MongoStorage


logger = logging.getLogger(__name__)


def _format_stats_text(row: Dict[str, Union[int, str, None]]) -> str:
    parts: List[str] = []

    ranking = row.get("ranking")
    if ranking is not None:
        parts.append(f"랭킹 : {format_korean_number(int(ranking))}")

    buff_score = row.get("buff_score")
    if buff_score is not None:
        parts.append(f"버프점수 : {int(buff_score):,}")

    party2 = row.get("party2")
    if party2 is not None:
        parts.append(f"2인 : {int(party2):,}")

    party4 = row.get("party4")
    if party4 is not None:
        parts.append(f"4인 : {int(party4):,}")

    return " ".join(parts)


def build_display_dataframe(rows: List[Dict[str, Union[int, str, None]]]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "닉네임": [row["nickname"] for row in rows],
            "스탯": [_format_stats_text(row) for row in rows],
        }
    )


def export_dataframe_image(df: pd.DataFrame, output_path: Path) -> None:
    df_reset = df.reset_index(drop=True)
    dataframe_image.export(
        df_reset, str(output_path), table_conversion="chrome", dpi=170
    )


async def delete_bot_messages(channel: discord.abc.Messageable, bot_user: discord.User) -> int:
    deleted = 0
    async for message in channel.history(limit=100):
        if message.author == bot_user:
            await message.delete()
            deleted += 1
    return deleted


async def send_account_images(
    channel: discord.abc.Messageable,
    storage: MongoStorage,
    accounts: Dict[str, List[str]],
    tmp_dir: Path,
) -> None:
    today = datetime.date.today().strftime("%Y년 %m월 %d일")
    logger.info("Preparing Discord images for %d accounts", len(accounts))

    for account_name, nicknames in accounts.items():
        logger.info("Building image for account=%s", account_name)
        rows = storage.load_account_stats(account_name, nicknames)
        df = build_display_dataframe(rows)
        image_filename = tmp_dir / f"{account_name}_table.png"

        export_dataframe_image(df, image_filename)
        logger.info("Image generated at %s", image_filename)
        try:
            with image_filename.open("rb") as handle:
                picture = discord.File(handle)
                await channel.send(
                    f"**{today} 기준 {account_name}의 캐릭터 정보**",
                    file=picture,
                )
            logger.info("Discord message sent for account=%s", account_name)
        finally:
            if image_filename.exists():
                image_filename.unlink()
                logger.info("Removed temp image %s", image_filename)


class DiscordBot(commands.Bot):
    def __init__(
        self,
        token: str,
        channel_id: int,
        storage: MongoStorage,
        accounts: Dict[str, List[str]],
        tmp_dir: Path,
    ) -> None:
        intents = discord.Intents.default()
        intents.messages = True
        intents.message_content = True
        super().__init__(command_prefix="!", intents=intents)

        self._token = token
        self._channel_id = channel_id
        self._storage = storage
        self._accounts = accounts
        self._tmp_dir = tmp_dir

    async def on_ready(self) -> None:
        logger.info("Discord bot logged in: %s", self.user)

        channel = self.get_channel(self._channel_id)
        if channel is None:
            logger.error("Discord channel not found: %s", self._channel_id)
            await self.close()
            return

        deleted = await delete_bot_messages(channel, self.user)
        logger.info("Deleted %d messages. Waiting 5 seconds before sending.", deleted)

        await asyncio.sleep(5)
        await send_account_images(channel, self._storage, self._accounts, self._tmp_dir)

        await asyncio.sleep(5)
        await self.close()
        logger.info("Discord bot shutdown complete")

    def run_bot(self) -> None:
        self.run(self._token)
