import logging
from datetime import datetime

from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup

from bot import BotClient
from bot.utils import reply_html, send_error, parse_iso8601_to_normal_date, \
    with_parsed_args, with_ensure_args
from bot.utils.message_helper import get_user_telegram_id
from config import config
from models.invite_code_model import InviteCodeType
from services import UserService

logger = logging.getLogger(__name__)


class UserCommandHandler:
    def __init__(self, bot_client: BotClient, user_service: UserService):
        self.bot_client = bot_client
        self.user_service = user_service
        self.code_to_message_id = {}
        logger.info("UserCommandHandler initialized")

    async def count(self, message: Message):
        """
        /count
        查询服务器内片子数量
        """
        try:
            count_data = self.user_service.emby_count()
            if not count_data:
                return await reply_html(message, "❌ 查询失败：无法获取数据")

            await reply_html(
                message,
                (
                    f"🎬 电影数量：<code>"
                    f"{count_data.get('MovieCount', 0)}"
                    f"</code>\n"
                    f"📽️ 剧集数量：<code>"
                    f"{count_data.get('SeriesCount', 0)}"
                    f"</code>\n"
                    f"🎞️ 总集数：<code>"
                    f"{count_data.get('EpisodeCount', 0)}"
                    f"</code>\n"
                )
            )
        except Exception as e:
            await send_error(message, e, prefix="查询失败")

    async def info(self, message: Message):
        """
        /info
        如果是私聊，查看自己信息；如果群里回复某人，则查看对方信息
        """
        telegram_id = await get_user_telegram_id(self.bot_client.client,
                                                 message)
        try:
            user, emby_info = await self.user_service.emby_info(telegram_id)
            last_active = (
                parse_iso8601_to_normal_date(emby_info.get("LastActivityDate"))
                if emby_info.get("LastActivityDate") else "无")
            date_created = parse_iso8601_to_normal_date(
                emby_info.get("DateCreated", ""))
            ban_status = "正常" if (
                    user.ban_time is None or user.ban_time == 0) else "已禁用"

            reply_text = (
                f"👤 <b>用户信息</b>：\n"
                f"• Emby用户名：<code>{user.emby_name}</code>\n"
                f"• 上次活动时间：<code>{last_active}</code>\n"
                f"• 创建时间：<code>{date_created}</code>\n"
                f"• 白名单：<code>{'是' if user.is_whitelist else '否'}</code>\n"
                f"• 管理员：<code>{'是' if user.is_admin else '否'}</code>\n"
                f"• 账号状态：<code>{ban_status}</code>\n"
            )

            if user.ban_time and user.ban_time > 0:
                ban_time = datetime.fromtimestamp(user.ban_time).strftime(
                    '%Y-%m-%d %H:%M:%S')
                reply_text += f"• 被ban时间：<code>{ban_time}</code>\n"
                if user.reason:
                    reply_text += f"• 被ban原因：<code>{user.reason}</code>\n"

            await reply_html(message, reply_text)
        except Exception as e:
            await send_error(message, e, prefix="查询失败")

    @with_parsed_args
    @with_ensure_args(1, "/use_code <邀请码>")
    async def use_code(self, message: Message, args: list[str]):
        """
        /use_code <邀请码>
        """
        code = args[0]
        telegram_id = message.from_user.id
        try:
            used_code = await self.user_service.redeem_code(telegram_id, code)
            if not used_code:
                return await reply_html(message, "❌ 邀请码使用失败")
            # 根据类型给出不同的回复
            if used_code.code_type == InviteCodeType.REGISTER:
                await reply_html(message,
                                 "✅ 邀请码使用成功，您已获得创建账号资格")
            else:
                await reply_html(message,
                                 "✅ 邀请码使用成功，您已获得白名单资格")

            # 如果该邀请码在bot中记录了消息，需要删除
            if self.code_to_message_id.get(code):
                code_to_message_id = self.code_to_message_id[code]
                await (
                    self.bot_client
                    .client.delete_messages(
                        code_to_message_id[0],
                        code_to_message_id[1])
                )
                del self.code_to_message_id[code]
        except Exception as e:
            await send_error(message, e, prefix="邀请码使用失败")

    async def select_line(self, message: Message):
        """
        /select_line
        用户选择线路（将返回可选线路按钮）。
        """
        try:
            telegram_id = message.from_user.id
            router_list = (
                    config.router_list or
                    await self.user_service.get_router_list(telegram_id)
            )
            # 缓存到 config 中，减少重复获取
            if router_list and not config.router_list:
                config.router_list = router_list

            user_router = await self.user_service.get_user_router(telegram_id)
            user_router_index = user_router.get('index', '')
            message_text = f"当前线路：<code>{user_router_index}</code>\n请选择线路："
            message_buttons = []

            for router in router_list:
                index = router.get('index')
                name = router.get('name')
                # 已选线路高亮
                button_text = f"🔵 {name}" if index == user_router_index \
                    else f"⚪ {name}"
                (
                    message_buttons
                    .append(
                        [InlineKeyboardButton(
                            button_text,
                            callback_data=f"SELECTROUTE_{index}")]
                    )
                )

            keyboard = InlineKeyboardMarkup(message_buttons)
            await reply_html(message, message_text, reply_markup=keyboard)
        except Exception as e:
            await send_error(message, e, prefix="查询失败")

    @with_parsed_args
    @with_ensure_args(1, "/create <用户名>")
    async def create_user(self, message: Message, args: list[str]):
        """
        /create <用户名>
        """
        emby_name = args[0]
        try:
            default_password = self.user_service.gen_default_passwd()
            user = await (
                self.user_service.emby_create_user(
                    message.from_user.id, emby_name, default_password
                )
            )
            if user and user.has_emby_account():
                await reply_html(
                    message,
                    f"✅ 创建用户成功。\n初始密码：<code>{default_password}</code>"
                )
            else:
                await reply_html(message, "❌ 创建用户失败，请稍后重试。")
        except Exception as e:
            await send_error(message, e, prefix="创建用户失败")

    async def reset_emby_password(self, message: Message):
        """
        /reset_emby_password
        """
        default_password = self.user_service.gen_default_passwd()
        try:
            if await (
                    self.user_service
                        .reset_password(
                            message.from_user.id, default_password
                    )
            ):
                await reply_html(
                    message,
                    f"✅ 密码重置成功。\n新密码：<code>{default_password}</code>"
                )
            else:
                await reply_html(message, "❌ 密码重置失败，请稍后重试。")
        except Exception as e:
            await send_error(message, e, prefix="密码重置失败")

    async def help_command(self, message: Message):
        """
        /help 或 /start
        查看命令帮助。
        """
        help_message = (
            "<b>用户命令：</b>\n"
            "/use_code [code] - 使用邀请码获取创建账号资格\n"
            "/create [username] - 创建Emby用户 (英文/下划线, 至少5位)\n"
            "/info - 查看用户信息（私聊查看自己的，群里可回复他人）\n"
            "/select_line - 选择线路\n"
            "/reset_emby_password - 重置Emby账号密码\n"
            "/count - 查看服务器内影片数量\n"
            "/help - 显示本帮助\n"
        )
        if await self.user_service.is_admin(message.from_user.id):
            help_message += (
                "\n<b>管理命令：</b>\n"
                "/new_code [数量] - 创建新的普通邀请码\n"
                "/new_whitelist_code [数量] - 创建新的白名单邀请码\n"
                "/register_until [YYYY-MM-DD HH:MM:SS] - 限时开放注册\n"
                "/register_amount [人数] - 开放指定注册名额\n"
                "/info (群里回复某人) - 查看他人信息\n"
                "/ban_emby [原因] - 禁用某用户的Emby账号\n"
                "/unban_emby - 解禁某用户的Emby账号\n"
            )
        await reply_html(message, help_message)
