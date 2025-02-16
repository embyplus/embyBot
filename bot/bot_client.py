import logging

from telethon.sync import TelegramClient

from config import config

logger = logging.getLogger(__name__)


class BotClient:
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        name="emby_bot",
    ):
        self.client = TelegramClient(name, api_id=api_id, api_hash=api_hash)
        logger.info(f"Bot client initialized with name: {name}")

    async def get_group_members(self, group_ids: list[int]):
        members = {}
        for group_id in group_ids:
            members[group_id] = {}
            async for member in self.client.iter_participants(int(group_id)):
                members[group_id][member.id] = member
        logger.debug(f"Fetched members for group ID: {group_id}")
        return members

    async def start(self):
        logger.info("Starting bot client")
        await self.client.start(bot_token=config.bot_token)
        await self.client.connect()

    def stop(self):
        logger.info("Stopping bot client")
        return self.client.disconnect()
