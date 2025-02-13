import logging
from datetime import datetime

from pyrogram.enums import ParseMode
from pyrogram.types import Message

from bot import BotClient
from bot.utils import with_parsed_args, reply_html, send_error, \
    with_ensure_args
from bot.utils.message_helper import get_user_telegram_id
from services import UserService

logger = logging.getLogger(__name__)


class AdminCommandHandler:
    def __init__(self, bot_client: BotClient, user_service: UserService):
        self.bot_client = bot_client
        self.user_service = user_service
        self.code_to_message_id = {}
        logger.info("AdminCommandHandler initialized")

    @with_parsed_args
    async def new_code(self, message: Message, args: list[str]):
        """
        /new_code [数量]
        """
        num = 1
        if args:
            try:
                num = int(args[0])
            except ValueError:
                return await reply_html(message,
                                        "❌ 请输入有效数量 /new_code [整数]")

        num = min(num, 20)
        try:
            code_list = await (
                self.user_service
                .create_invite_code(message.from_user.id, num)
            )
            await self.send_code(code_list, message)
        except Exception as e:
            await send_error(message, e, prefix="创建邀请码失败")

    @with_parsed_args
    async def new_whitelist_code(self, message: Message, args: list[str]):
        """
        /new_whitelist_code [数量]
        """
        num = 1
        if args:
            try:
                num = int(args[0])
            except ValueError:
                return await reply_html(
                    message,
                    "❌ 请输入有效数量 /new_whitelist_code [整数]")

        num = min(num, 20)
        try:
            code_list = await self.user_service.create_whitelist_code(
                message.from_user.id, num)
            await self.send_code(code_list, message, whitelist=True)
        except Exception as e:
            await send_error(message, e, prefix="创建白名单邀请码失败")

    async def send_code(self, code_list, message, whitelist: bool = False):
        if whitelist:
            base_text = "📌 白名单邀请码：\n点击复制👉"
        else:
            base_text = "📌 邀请码：\n点击复制👉"
        for code_obj in code_list:
            # 每次用 base_text 重置消息文本哦～
            message_text = f"{base_text}<code>{code_obj.code}</code>"
            if message.reply_to_message is not None:
                await self.bot_client.client.send_message(
                    chat_id=message.from_user.id,
                    text=message_text,
                    parse_mode=ParseMode.HTML,
                )
                await self.bot_client.client.send_message(
                    chat_id=message.reply_to_message.from_user.id,
                    text=message_text,
                    parse_mode=ParseMode.HTML,
                )
                await reply_html(message, "✅ 已发送邀请码")
            else:
                msg = await reply_html(
                    message,
                    message_text
                )
                self.code_to_message_id[code_obj.code] = (
                    message.chat.id, msg.id
                )

    @with_parsed_args
    async def ban_emby(self, message: Message, args: list[str]):
        """
        /ban_emby [原因] (群里需回复某人或手动指定)
        """
        reason = args[0] if args else "管理员禁用"

        operator_id = message.from_user.id
        telegram_id = await get_user_telegram_id(self.bot_client.client,
                                                 message)
        try:
            if await self.user_service.emby_ban(telegram_id, reason,
                                                operator_id):
                await reply_html(
                    message,
                    f"✅ 已禁用用户 <code>{telegram_id}</code> 的Emby账号"
                )
            else:
                await reply_html(message, "❌ 禁用失败，请稍后重试。")
        except Exception as e:
            await send_error(message, e, prefix="禁用失败")

    async def unban_emby(self, message: Message):
        """
        /unban_emby (群里需回复某人或手动指定)
        """
        operator_id = message.from_user.id
        telegram_id = await get_user_telegram_id(self.bot_client.client,
                                                 message)
        try:
            if await self.user_service.emby_unban(telegram_id, operator_id):
                await reply_html(
                    message,
                    f"✅ 已解禁用户 <code>{telegram_id}</code> 的Emby账号"
                )
            else:
                await reply_html(message, "❌ 解禁失败，请稍后重试。")
        except Exception as e:
            await send_error(message, e, prefix="解禁失败")

    @with_parsed_args
    @with_ensure_args(2, "/register_until 2023-10-01 12:00:00")
    async def register_until(self, message: Message, args: list[str]):
        """
        /register_until <时间: YYYY-MM-DD HH:MM:SS>
        限时开放注册
        """
        time_str = " ".join(args)
        try:
            time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            if time < now:
                return await reply_html(message, "❌ 时间必须晚于当前时间")

            await self.user_service.set_emby_config(
                message.from_user.id,
                register_public_time=int(time.timestamp())
            )
            await reply_html(
                message,
                f"✅ 已开放注册，截止时间：<code>{time_str}</code>"
            )
        except Exception as e:
            await send_error(message, e, prefix="开放注册失败")

    @with_parsed_args
    @with_ensure_args(1, "/register_amount <人数>")
    async def register_amount(self, message: Message, args: list[str]):
        """
        /register_amount <人数>
        开放指定数量的注册名额
        """
        try:
            amount = int(args[0])
            await self.user_service.set_emby_config(
                message.from_user.id,
                register_public_user=amount
            )
            await reply_html(
                message,
                f"✅ 已开放注册，名额：<code>{amount}</code>"
            )
        except Exception as e:
            await send_error(message, e, prefix="开放注册失败")
