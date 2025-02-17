import logging

from telethon import events

from config import config
from services import UserService

logger = logging.getLogger(__name__)


async def user_in_group_on_filter(update: events.NewMessage.Event) -> bool:
    telegram_id = update.sender_id
    if config.group_members and telegram_id in config.group_members:
        logger.debug(f"User {telegram_id} is in group")
        return True
    # if config.channel_members and telegram_id in config.channel_members:
    #     logger.debug(f"User {telegram_id} is in channel")
    #     return True

    logger.debug(f"User {telegram_id} is not in group or channel")
    return False


async def admin_user_on_filter(update: events.NewMessage.Event) -> bool:
    telegram_id = update.sender_id
    try:
        user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
        if user.is_admin:
            logger.debug(f"User {telegram_id} is an admin")
            return True
    except Exception as e:
        logger.error(
            f"Error checking admin status for user {telegram_id}: {e}", exc_info=True
        )
        return False

    logger.debug(f"User {telegram_id} is not an admin")
    return False


async def emby_user_on_filter(update: events.NewMessage.Event) -> bool:
    telegram_id = update.sender_id
    try:
        user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
        if user.has_emby_account() and not user.is_emby_baned():
            logger.debug(f"User {telegram_id} is an Emby user")
            return True
    except Exception as e:
        logger.error(
            f"Error checking Emby status for user {telegram_id}: {e}", exc_info=True
        )
        return False

    logger.debug(f"User {telegram_id} is not an Emby user")
    return False


async def is_private_and_group_emby_message(message):
    """
    检查消息是否符合以下条件：
    1. 是私有消息
    2. 用户在指定的群组内
    3. 用户是 Emby 用户
    """
    return (
        message.is_private
        and await user_in_group_on_filter(message)
        and await emby_user_on_filter(message)
    )
