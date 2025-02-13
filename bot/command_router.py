from pyrogram import filters

from bot import BotClient
from bot.command.admin_command import AdminCommandHandler
from bot.command.event_command import EventHandler
from bot.command.user_command import UserCommandHandler
from bot.utils.filters import user_in_group_on_filter, emby_user_on_filter, \
    admin_user_on_filter


def setup_command_routes(bot_client: BotClient,
                         user_command_handler: UserCommandHandler,
                         admin_command_handler: AdminCommandHandler,
                         event_handler: EventHandler):
    # 定义命令配置，每项为 (命令, 过滤器, 处理函数)
    command_definitions = [
        (
            ["help", "start"],
            filters.private,
            user_command_handler.help_command
        ),
        ("count", user_in_group_on_filter, user_command_handler.count),
        ("info", user_in_group_on_filter, user_command_handler.info),
        ("use_code", filters.private & user_in_group_on_filter,
         user_command_handler.use_code),
        ("create", filters.private & user_in_group_on_filter,
         user_command_handler.create_user),
        ("reset_emby_password",
         filters.private & user_in_group_on_filter & emby_user_on_filter,
         user_command_handler.reset_emby_password),
        ("select_line",
         filters.private & user_in_group_on_filter & emby_user_on_filter,
         user_command_handler.select_line),
        ("new_code", admin_user_on_filter, admin_command_handler.new_code),
        ("new_whitelist_code", admin_user_on_filter,
         admin_command_handler.new_whitelist_code),
        ("ban_emby", admin_user_on_filter, admin_command_handler.ban_emby),
        ("unban_emby", admin_user_on_filter, admin_command_handler.unban_emby),
        ("register_until", admin_user_on_filter,
         admin_command_handler.register_until),
        ("register_amount", admin_user_on_filter,
         admin_command_handler.register_amount),
    ]

    # 循环注册消息处理器
    for cmd, f, func in command_definitions:
        if isinstance(cmd, list):
            # 对于多个命令，一般只用于私聊
            def make_handler(func_=func, f_=f, cmd_=None):
                if cmd_ is None:
                    cmd_ = cmd

                @bot_client.client.on_message(
                    filters.private & filters.command(cmd_) & f_)
                async def handler(_, message):
                    await func_(message)

                return handler

            make_handler()
        else:
            def make_handler(func_=func, f_=f, cmd_=cmd):
                @bot_client.client.on_message(filters.command(cmd_) & f_)
                async def handler(_, message):
                    await func_(message)

                return handler

            make_handler()

    # 注册回调查询处理器
    @bot_client.client.on_callback_query()
    async def c_select_line_cb(client, callback_query):
        await event_handler.handle_callback_query(client, callback_query)

    # 注册群组成员变动处理器
    @bot_client.client.on_message(
        filters.left_chat_member | filters.new_chat_members)
    async def group_member_change_handler(client, message):
        await event_handler.group_member_change_handler(client, message)
