import logging

from pyrogram.filters import create

from config import config
from services import UserService

logger = logging.getLogger(__name__)


async def check_group_membership(client, message) -> bool:
    """检查用户是否在任一配置中的群聊中。"""
    user_id = message.from_user.id
    for group_id in config.telegram_group_ids:
        try:
            member = await client.get_chat_member(group_id, user_id)
            if member and member.status:
                logger.debug(f"用户 {user_id} 已加入群 {group_id}")
                return True
        except Exception as e:
            logger.debug(f"查询用户 {user_id} 在群 {group_id} 的信息失败：{e}")
            continue
    return False


def user_in_group_on_filter():
    """自定义过滤器：判断用户是否在指定群组中；如果不在则回复提示。"""
    async def custom_filter(flt, client, message):
        if await check_group_membership(client, message):
            return True
        try:
            await message.reply("❌ 请先加入指定的群聊后再使用本命令。")
        except Exception as exc:
            logger.error(f"回复提示消息失败：{exc}")
        return False
    return create(custom_filter)


async def admin_user_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    try:
        user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
        if user.is_admin:
            logger.debug(f"User {telegram_id} is an admin")
            return True
    except Exception as e:
        logger.error(f"Error checking admin status for user {telegram_id}: {e}", exc_info=True)
        return False

    logger.debug(f"User {telegram_id} is not an admin")
    return False


async def emby_user_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    try:
        user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
        if user.has_emby_account() and not user.is_emby_baned():
            logger.debug(f"User {telegram_id} is an Emby user")
            return True
    except Exception as e:
        logger.error(f"Error checking Emby status for user {telegram_id}: {e}", exc_info=True)
        return False

    logger.debug(f"User {telegram_id} is not an Emby user")
    return False


admin_user_on_filter = create(admin_user_on_filter, "admin_user_on_filter")
emby_user_on_filter = create(emby_user_on_filter, "emby_user_on_filter")
