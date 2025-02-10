import logging

from pyrogram.filters import create

from config import config
from services import UserService

logger = logging.getLogger(__name__)


async def user_in_group_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    if config.group_members and telegram_id in config.group_members:
        logger.debug(f"User {telegram_id} is in group")
        return True
    if config.channel_members and telegram_id in  config.channel_members:
        logger.debug(f"User {telegram_id} is in channel")
        return True

    logger.debug(f"User {telegram_id} is not in group or channel")
    return False


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


user_in_group_on_filter = create(user_in_group_on_filter, 'user_in_group_on_filter')
admin_user_on_filter = create(admin_user_on_filter, 'admin_user_on_filter')
emby_user_on_filter = create(emby_user_on_filter, 'emby_user_on_filter')