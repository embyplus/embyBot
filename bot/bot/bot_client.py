from pyrogram import Client, idle


class BotClient:
    def __init__(
            self,
            api_id: str,
            api_hash: str,
            bot_token: str,
            name="emby_bot",
    ):
        self.client = Client(
            name=name,
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token
        )

    async def get_group_members(self, group_ids: list[int]):
        members = {}
        for group_id in group_ids:
            members[group_id] = {}
            async for member in self.client.get_chat_members(int(group_id)):
                members[group_id][member.user.id] = member.user
        return members

    async def start(self):
        return await self.client.start()

    @staticmethod
    async def idle():
        return await idle()

    def stop(self):
        return self.client.stop()
