import logging

from telethon import events
from telethon.errors import UsernameInvalidError, PeerIdInvalidError

from config import config

logger = logging.getLogger(__name__)


async def get_user_telegram_id(client, message: events.NewMessage.Event):
    # 默认获取自己的 ID
    telegram_id = message.sender_id
    telegram_username = None
    logger.debug(f"Default Telegram ID: {telegram_id}")

    # 如果回复了别人，获取被回复用户的 ID
    if message.message.is_reply:
        reply_message = await message.message.get_reply_message()
        telegram_id = reply_message.sender_id
        logger.debug(f"Telegram ID from replied message: {telegram_id}")

    # 如果有额外参数
    args = message.text.split(" ")
    if len(args) > 1:
        telegram_str = args[1]

        # 直接提供 Telegram ID（纯数字）
        if telegram_str.isdigit():
            telegram_id = int(telegram_str)
            logger.debug(f"Telegram ID from arguments (numeric): {telegram_id}")

        # 使用 @username
        elif telegram_str.startswith("@"):
            telegram_username = telegram_str[1:]  # 去掉 `@`
            logger.debug(f"Telegram username from arguments: {telegram_username}")

    # 通过用户名查找 ID
    if telegram_username:
        try:
            user = await client.get_entity(telegram_username)
            if user.id != int(config.bot_token.split(":")[0]):
                telegram_id = user.id
                logger.debug(
                    f"Telegram ID resolved from username {telegram_username}: {telegram_id}"
                )
        except UsernameInvalidError:
            error_message = f"❌ 用户名 @{telegram_username} 不存在"
            logger.warning(f"Username not occupied: {telegram_username}")
            await message.reply(error_message)
            return None
        except PeerIdInvalidError:
            error_message = f"❌ 无法获取用户 @{telegram_username} 的 ID"
            logger.warning(f"Peer ID invalid for username: {telegram_username}")
            await message.reply(error_message)
            return None
        except Exception as e:
            logger.error(
                f"Error getting user ID from username {telegram_username}: {e}",
                exc_info=True,
            )
            return None

    return telegram_id
