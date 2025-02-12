import logging

from pyrogram import Client, idle

logger = logging.getLogger(__name__)


class BotClient:
    def __init__(
        self,
        api_id: str,
        api_hash: str,
        bot_token: str,
        name="emby_bot",
    ):
        self.client = Client(
            name=name, api_id=api_id, api_hash=api_hash, bot_token=bot_token
        )
        logger.info(f"Bot client initialized with name: {name}")

    async def get_group_members(self, group_ids: list[int]):
        members = {}
        for group_id in group_ids:
            members[group_id] = {}
            async for member in self.client.get_chat_members(int(group_id)):
                members[group_id][member.user.id] = member.user
        logger.debug(f"Fetched members for group ID: {group_id}")
        return members

    async def start(self):
        logger.info("Starting bot client")
        return await self.client.start()

    @staticmethod
    async def idle():
        logger.info("Bot client is now idle")
        return await idle()

    def stop(self):
        logger.info("Stopping bot client")
        return self.client.stop()
