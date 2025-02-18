import functools
import logging
from datetime import datetime
from typing import Union

from telethon import events, Button
from telethon.tl.types import (
    MessageActionChatAddUser,
    MessageActionChatDeleteUser,
    MessageActionChatJoinedByLink,
)

from bot.bot_client import BotClient
from bot.filters import (
    user_in_group_on_filter,
    admin_user_on_filter,
    is_private_and_group_emby_message,
)
from bot.message_helper import get_user_telegram_id
from bot.utils import parse_iso8601_to_normal_date
from config import config
from models.invite_code_model import InviteCodeType
from services import UserService

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, bot_client: BotClient, user_service: UserService):
        self.bot_client = bot_client
        self.user_service = user_service
        self.code_to_message_id = {}
        logger.info("CommandHandler initialized")

    # =============== 辅助方法 ===============

    @staticmethod
    async def _reply_html(message, text: str, **kwargs):
        """
        统一回复方法，使用 HTML parse_mode。
        """
        return await message.reply(text, parse_mode="HTML", **kwargs)

    @staticmethod
    def _parse_args(message: events.NewMessage.Event) -> list[str]:
        """
        将用户输入拆分为命令 + 参数列表，如：
        '/create testuser' -> ['testuser']
        """
        parts = message.text.strip().split(" ")
        return parts[1:] if len(parts) > 1 else []

    @staticmethod
    def ensure_args(min_len: int, usage: str):
        """
        装饰器：确保命令行参数长度足够，不足则回复用法说明。
        """

        def decorator(func):
            @functools.wraps(func)
            async def wrapper(self, message, *args, **kwargs):
                # 从消息中解析参数
                parsed_args = self._parse_args(message)
                if len(parsed_args) < min_len:
                    await self._reply_html(
                        message, f"参数不足，请参考用法：\n<code>{usage}</code>"
                    )
                    return
                # 将解析好的参数传递给目标函数，避免在函数内部再调用 _parse_args
                return await func(self, message, parsed_args, *args, **kwargs)

            return wrapper

        return decorator

    async def _send_error(
        self,
        message: events.NewMessage.Event,
        error: Exception,
        prefix: str = "操作失败",
    ):
        """
        统一的异常捕获后回复方式。
        """
        logger.error(f"{prefix}：{error}", exc_info=True)
        await self._reply_html(message, f"{prefix}：{error}")

    # =============== 各类命令逻辑 ===============

    @ensure_args(1, "/create <用户名>")
    async def create_user(self, message: events.NewMessage.Event, args: list[str]):
        """
        /create <用户名>
        """

        emby_name = args[0]
        try:
            default_password = self.user_service.gen_default_passwd()
            user = await self.user_service.emby_create_user(
                message.sender_id, emby_name, default_password
            )
            if user and user.has_emby_account():
                await self._reply_html(
                    message,
                    f"✅ 创建用户成功。\n初始密码：<code>{default_password}</code>",
                )
            else:
                await self._reply_html(message, "❌ 创建用户失败，请稍后重试。")
        except Exception as e:
            await self._send_error(message, e, prefix="创建用户失败")

    async def info(self, message: events.NewMessage.Event):
        """
        /info
        如果是私聊，查看自己信息；如果群里回复某人，则查看对方信息
        """
        telegram_id = await get_user_telegram_id(self.bot_client.client, message)
        try:
            user, emby_info = await self.user_service.emby_info(telegram_id)
            last_active = (
                parse_iso8601_to_normal_date(emby_info.get("LastActivityDate"))
                if emby_info.get("LastActivityDate")
                else "无"
            )
            date_created = parse_iso8601_to_normal_date(
                emby_info.get("DateCreated", "")
            )
            ban_status = (
                "正常" if (user.ban_time is None or user.ban_time == 0) else "已禁用"
            )

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
                    "%Y-%m-%d %H:%M:%S"
                )
                reply_text += f"• 被ban时间：<code>{ban_time}</code>\n"
                if user.reason:
                    reply_text += f"• 被ban原因：<code>{user.reason}</code>\n"

            await self._reply_html(message, reply_text)
        except Exception as e:
            await self._send_error(message, e, prefix="查询失败")

    @ensure_args(1, "/use_code <邀请码>")
    async def use_code(self, message: events.NewMessage.Event, args: list[str]):
        """
        /use_code <邀请码>
        """

        code = args[0]
        telegram_id = message.sender_id
        try:
            used_code = await self.user_service.redeem_code(telegram_id, code)
            if not used_code:
                return await self._reply_html(message, "❌ 邀请码使用失败")
            # 根据类型给出不同的回复
            if used_code.code_type == InviteCodeType.REGISTER:
                await self._reply_html(
                    message, "✅ 邀请码使用成功，您已获得创建账号资格"
                )
            else:
                await self._reply_html(message, "✅ 邀请码使用成功，您已获得白名单资格")

            # 如果该邀请码在bot中记录了消息，需要删除
            if self.code_to_message_id.get(code):
                code_to_message_id = self.code_to_message_id[code]
                await self.bot_client.client.delete_messages(
                    code_to_message_id[0], code_to_message_id[1]
                )
                del self.code_to_message_id[code]
        except Exception as e:
            await self._send_error(message, e, prefix="邀请码使用失败")

    async def reset_emby_password(self, message: events.NewMessage.Event):
        """
        /reset_emby_password
        """
        default_password = self.user_service.gen_default_passwd()
        try:
            if await self.user_service.reset_password(
                message.sender_id, default_password
            ):
                await self._reply_html(
                    message,
                    f"✅ 密码重置成功。\n新密码：<code>{default_password}</code>",
                )
            else:
                await self._reply_html(message, "❌ 密码重置失败，请稍后重试。")
        except Exception as e:
            await self._send_error(message, e, prefix="密码重置失败")

    async def new_code(self, message: events.NewMessage.Event):
        """
        /new_code [数量]
        """
        args = self._parse_args(message)
        num = 1
        if args:
            try:
                num = int(args[0])
            except ValueError:
                return await self._reply_html(
                    message, "❌ 请输入有效数量 /new_code [整数]"
                )

        num = min(num, 20)
        try:
            code_list = await self.user_service.create_invite_code(
                message.sender_id, num
            )
            for code_obj in code_list:
                message_text = f"📌 邀请码：\n点击复制👉<code>{code_obj.code}</code>"
                await self.reply_user_after_create_code(code_obj, message, message_text)
        except Exception as e:
            await self._send_error(message, e, prefix="创建邀请码失败")

    async def reply_user_after_create_code(self, code_obj, message, message_text):
        if message.message.is_reply:
            reply_message = await message.message.get_reply_message()
            await self.bot_client.client.send_message(
                chat_id=message.sender_id, text=message_text, parse_mode="HTML"
            )
            await self.bot_client.client.send_message(
                chat_id=reply_message.sender_id,
                text=message_text,
                parse_mode="HTML",
            )
            await self._reply_html(message, "✅ 已发送邀请码")
        else:
            # 如果不是回复消息，直接回复给当前发件人
            msg = await self._reply_html(message, message_text)
            # 保存发件人 ID 和消息 ID
            self.code_to_message_id[code_obj.code] = (message.sender_id, msg.id)

    async def new_whitelist_code(self, message: events.NewMessage.Event):
        """
        /new_whitelist_code [数量]
        """
        args = self._parse_args(message)
        num = 1
        if args:
            try:
                num = int(args[0])
            except ValueError:
                return await self._reply_html(
                    message, "❌ 请输入有效数量 /new_whitelist_code [整数]"
                )

        num = min(num, 20)
        try:
            code_list = await self.user_service.create_whitelist_code(
                message.sender_id, num
            )
            for code_obj in code_list:
                message_text = (
                    f"📌 白名单邀请码：\n点击复制👉<code>{code_obj.code}</code>"
                )
                await self.reply_user_after_create_code(code_obj, message, message_text)
        except Exception as e:
            await self._send_error(message, e, prefix="创建白名单邀请码失败")

    async def ban_emby(self, message: events.NewMessage.Event):
        """
        /ban_emby [原因] (群里需回复某人或手动指定)
        """
        args = self._parse_args(message)
        reason = args[0] if args else "管理员禁用"

        operator_id = message.sender_id
        telegram_id = await get_user_telegram_id(self.bot_client.client, message)
        try:
            if await self.user_service.emby_ban(telegram_id, reason, operator_id):
                await self._reply_html(
                    message, f"✅ 已禁用用户 <code>{telegram_id}</code> 的Emby账号"
                )
            else:
                await self._reply_html(message, "❌ 禁用失败，请稍后重试。")
        except Exception as e:
            await self._send_error(message, e, prefix="禁用失败")

    async def unban_emby(self, message: events.NewMessage.Event):
        """
        /unban_emby (群里需回复某人或手动指定)
        """
        operator_id = message.sender_id
        telegram_id = await get_user_telegram_id(self.bot_client.client, message)
        try:
            if await self.user_service.emby_unban(telegram_id, operator_id):
                await self._reply_html(
                    message, f"✅ 已解禁用户 <code>{telegram_id}</code> 的Emby账号"
                )
            else:
                await self._reply_html(message, "❌ 解禁失败，请稍后重试。")
        except Exception as e:
            await self._send_error(message, e, prefix="解禁失败")

    async def select_line(self, message: events.NewMessage.Event):
        """
        /select_line
        用户选择线路（将返回可选线路按钮）。
        """
        try:
            telegram_id = message.sender_id
            router_list = config.router_list or await self.user_service.get_router_list(
                telegram_id
            )
            # 缓存到 config 中，减少重复获取
            if router_list and not config.router_list:
                config.router_list = router_list

            user_router = await self.user_service.get_user_router(telegram_id)
            user_router_index = user_router.get("index", "")
            message_text = f"当前线路：<code>{user_router_index}</code>\n请选择线路："
            message_buttons = []

            for router in router_list:
                index = router.get("index")
                name = router.get("name")
                # 已选线路高亮
                button_text = (
                    f"🔵 {name}" if index == user_router_index else f"⚪ {name}"
                )
                message_buttons.append(
                    [Button.inline(button_text, f"SELECTROUTE_{index}")]
                )
            await self._reply_html(message, message_text, buttons=message_buttons)
        except Exception as e:
            await self._send_error(message, e, prefix="查询失败")

    async def group_member_change_handler(
            self,
            message: Union[
                MessageActionChatAddUser,
                MessageActionChatDeleteUser,
                MessageActionChatJoinedByLink,
            ],
    ):
        """
        群组成员变动处理器。
        """
        if message.user_id:
            left_member_id = message.user_id
            left_member = await self.user_service.must_get_user(left_member_id)
            if (
                left_member.has_emby_account()
                and not left_member.is_emby_baned()
                and not left_member.is_whitelist
            ):
                await self.user_service.emby_ban(message.user_id, "用户已退出群组")
            config.group_members.pop(message.user_id, None)
        if message.users:
            for new_member in message.users:
                config.group_members[new_member.id] = new_member

    async def handle_callback_query(self, callback_query: events.CallbackQuery.Event):
        """
        回调按钮事件统一处理，如切换线路。
        """
        data = callback_query.data.decode().split("_")
        if data[0] == "SELECTROUTE":
            index = data[1]
            try:
                if not config.router_list:
                    await callback_query.answer("尚未加载线路列表，请稍后重试")
                    return

                selected_router = next(
                    (r for r in config.router_list if r["index"] == index), None
                )
                if not selected_router:
                    await callback_query.answer("线路不存在")
                    return

                await self.user_service.update_user_router(
                    callback_query.sender_id, index
                )
                await callback_query.answer("线路已更新")
                await callback_query.edit(
                    f"已选择 <b>{selected_router['name']}</b>\n"
                    "生效可能会有 30 秒延迟，请耐心等候。",
                    parse_mode="HTML",
                )
            except Exception as e:
                await callback_query.answer(f"操作失败：{str(e)}", alert=True)
                logger.error(f"Callback query failed: {e}", exc_info=True)

    async def count(self, message: events.NewMessage.Event):
        """
        /count
        查询服务器内片子数量
        """
        try:
            count_data = self.user_service.emby_count()
            if not count_data:
                return await self._reply_html(message, "❌ 查询失败：无法获取数据")

            await self._reply_html(
                message,
                (
                    f"🎬 电影数量：<code>{count_data.get('MovieCount', 0)}</code>\n"
                    f"📽️ 剧集数量：<code>{count_data.get('SeriesCount', 0)}</code>\n"
                    f"🎞️ 总集数：<code>{count_data.get('EpisodeCount', 0)}</code>\n"
                ),
            )
        except Exception as e:
            await self._send_error(message, e, prefix="查询失败")

    @ensure_args(2, "/register_until 2023-10-01 12:00:00")
    async def register_until(self, message: events.NewMessage.Event, args: list[str]):
        """
        /register_until <时间: YYYY-MM-DD HH:MM:SS>
        限时开放注册
        """

        time_str = " ".join(args)
        try:
            time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
            now = datetime.now()
            if time < now:
                return await self._reply_html(message, "❌ 时间必须晚于当前时间")

            await self.user_service.set_emby_config(
                message.sender_id, register_public_time=int(time.timestamp())
            )
            await self._reply_html(
                message, f"✅ 已开放注册，截止时间：<code>{time_str}</code>"
            )
        except Exception as e:
            await self._send_error(message, e, prefix="开放注册失败")

    @ensure_args(1, "/register_amount <人数>")
    async def register_amount(self, message: events.NewMessage.Event, args: list[str]):
        """
        /register_amount <人数>
        开放指定数量的注册名额
        """

        try:
            amount = int(args[0])
            await self.user_service.set_emby_config(
                message.sender_id, register_public_user=amount
            )
            await self._reply_html(
                message, f"✅ 已开放注册，名额：<code>{amount}</code>"
            )
        except Exception as e:
            await self._send_error(message, e, prefix="开放注册失败")

    async def help_command(self, message):
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
        if await self.user_service.is_admin(message.sender_id):
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
        await self._reply_html(message, help_message)

    # =============== 命令挂载 ===============
    def setup_commands(self):
        @self.bot_client.client.on(events.NewMessage(pattern="/start"))
        @self.bot_client.client.on(events.NewMessage(pattern="/help"))
        async def c_help(message):
            await self.help_command(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/count", func=user_in_group_on_filter)
        )
        async def c_count(message):
            await self.count(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/info", func=user_in_group_on_filter)
        )
        async def c_info(message):
            await self.info(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/use_code", func=user_in_group_on_filter)
        )
        async def c_use_code(message):
            await self.use_code(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/create", func=user_in_group_on_filter)
        )
        async def c_create_user(message):
            await self.create_user(message)

        @self.bot_client.client.on(
            events.NewMessage(
                pattern="/reset_emby_password",
                func=is_private_and_group_emby_message,
            )
        )
        async def c_reset_emby_password(message):
            await self.reset_emby_password(message)

        @self.bot_client.client.on(
            events.NewMessage(
                pattern="/select_line",
                func=is_private_and_group_emby_message,
            )
        )
        async def c_select_line(message):
            await self.select_line(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/new_code", func=admin_user_on_filter)
        )
        async def c_new_code(message):
            await self.new_code(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/new_whitelist_code", func=admin_user_on_filter)
        )
        async def c_new_whitelist_code(message):
            await self.new_whitelist_code(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/ban_emby", func=admin_user_on_filter)
        )
        async def c_ban_emby(message):
            await self.ban_emby(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/unban_emby", func=admin_user_on_filter)
        )
        async def c_unban_emby(message):
            await self.unban_emby(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/register_until", func=admin_user_on_filter)
        )
        async def c_register_until(message):
            await self.register_until(message)

        @self.bot_client.client.on(
            events.NewMessage(pattern="/register_amount", func=admin_user_on_filter)
        )
        async def c_register_amount(message):
            await self.register_amount(message)

        @self.bot_client.client.on(events.CallbackQuery)
        async def c_select_line_cb(callback_query: events.CallbackQuery.Event):
            await self.handle_callback_query(callback_query)

        @self.bot_client.client.on(
            events.ChatAction(
                func=lambda message: message.user_joined
                or message.user_added
                or message.user_left
                or message.user_kicked
            )
        )
        async def group_member_change_handler(message):
            await self.group_member_change_handler(message)
