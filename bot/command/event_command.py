import logging

from pyrogram.types import Message, CallbackQuery

from bot import BotClient
from config import config
from services import UserService

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, bot_client: BotClient, user_service: UserService):
        self.bot_client = bot_client
        self.user_service = user_service
        self.code_to_message_id = {}
        logger.info("EventHandler initialized")

    async def handle_callback_query(self, _,
                                    callback_query: CallbackQuery):
        """
        回调按钮事件统一处理，如切换线路。
        """
        data = callback_query.data.split('_')
        if data[0] == 'SELECTROUTE':
            index = data[1]
            try:
                if not config.router_list:
                    await callback_query.answer("尚未加载线路列表，请稍后重试")
                    return

                selected_router = next(
                    (r for r in config.router_list if r['index'] == index),
                    None)
                if not selected_router:
                    await callback_query.answer("线路不存在")
                    return

                await self.user_service.update_user_router(
                    callback_query.from_user.id, index)
                await callback_query.answer("线路已更新")
                await callback_query.message.edit(
                    f"已选择 <b>{selected_router['name']}</b>\n"
                    "生效可能会有 30 秒延迟，请耐心等候。"
                )
            except Exception as e:
                await callback_query.answer(f"操作失败：{str(e)}",
                                            show_alert=True)
                logger.error(f"Callback query failed: {e}", exc_info=True)

    async def group_member_change_handler(self, _, message: Message):
        """
        群组成员变动处理器。
        """
        if message.left_chat_member:
            left_member_id = message.left_chat_member.id
            left_member = await self.user_service.must_get_user(left_member_id)
            if (left_member.has_emby_account()
                    and not left_member.is_emby_baned()
                    and not left_member.is_whitelist):
                await self.user_service.emby_ban(message.left_chat_member.id,
                                                 "用户已退出群组")
            config.group_members.pop(message.left_chat_member.id, None)
        if message.new_chat_members:
            for new_member in message.new_chat_members:
                config.group_members[new_member.id] = new_member
