from pyrogram.filters import create

from config import config
from services import UserService


async def user_in_group_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    if config.group_members and config.group_members[telegram_id]:
        return True
    if config.channel_members and config.channel_members[telegram_id]:
        return True

    return False


async def admin_user_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
    if user.is_admin:
        return True

    return False


async def emby_user_on_filter(filter, client, update) -> bool:
    user = update.from_user or update.sender_chat
    telegram_id = user.id
    user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
    if user.has_emby_account() and not user.is_emby_baned():
        return True

    return False


user_in_group_on_filter = create(user_in_group_on_filter, 'user_in_group_on_filter')
admin_user_on_filter = create(admin_user_on_filter, 'admin_user_on_filter')
emby_user_on_filter = create(emby_user_on_filter, 'emby_user_on_filter')
