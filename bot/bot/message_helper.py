from pyrogram.errors import UsernameNotOccupied, PeerIdInvalid


async def get_user_telegram_id(client, message):
    # 默认获取自己的 ID
    telegram_id = message.from_user.id
    telegram_username = None

    # 如果回复了别人，获取被回复用户的 ID
    if message.reply_to_message:
        telegram_id = message.reply_to_message.from_user.id

    # 如果有额外参数
    args = message.text.split(" ")
    if len(args) > 1:
        telegram_str = args[1]

        # 直接提供 Telegram ID（纯数字）
        if telegram_str.isdigit():
            telegram_id = int(telegram_str)

        # 使用 @username
        elif telegram_str.startswith("@"):
            telegram_username = telegram_str[1:]  # 去掉 `@`

    # 通过用户名查找 ID
    if telegram_username:
        try:
            user = await client.get_users(telegram_username)
            telegram_id = user.id
        except UsernameNotOccupied:
            return await message.reply(f"❌ 用户名 @{telegram_username} 不存在")
        except PeerIdInvalid:
            return await message.reply(f"❌ 无法获取用户 @{telegram_username} 的 ID")
    return telegram_id
