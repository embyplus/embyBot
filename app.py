import asyncio
import logging
from datetime import datetime

import pytz

from bot.bot_client import BotClient
from bot.commands import CommandHandler
from config import config
from core.emby_api import EmbyApi, EmbyRouterAPI
from services import UserService
from models.database import (
    init_db,
    create_database_if_not_exists,
    create_tables,
)

# Initialize logger
logger = logging.getLogger(__name__)
# <CURRENT_CURSOR_POSITION>


async def _init_db() -> None:
    """初始化数据库连接并创建表。"""
    # Create database if it doesn't exist
    await create_database_if_not_exists(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_pass,
        db_name=config.db_name,
    )

    # Initialize the engine and session factory
    await init_db(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_pass,
        db_name=config.db_name,
        echo=True,
    )

    # Create all tables
    await create_tables()


def _init_logger() -> None:
    """初始化日志记录器。"""
    # Clear any existing handlers to prevent duplicates
    logger.handlers = []

    # Create handlers
    handler = logging.StreamHandler()  # 输出到终端
    fmt = "%(levelname)s [%(asctime)s] %(name)s - %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(
        fmt=fmt,
        datefmt=datefmt,
    )
    handler.setFormatter(formatter)

    # Set log level
    logger.setLevel(config.log_level)

    # Add handler (don't use basicConfig if you're manually configuring)
    logger.addHandler(handler)

    # Add file handler if needed
    file_handler = logging.FileHandler("default.log")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


def _init_tz() -> None:
    """初始化时区设置。"""
    if config.timezone:
        try:
            timezone = pytz.timezone(config.timezone)
            now = datetime.now(timezone).strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"时区已设置为: {config.timezone}，当前时间: {now}")
        except pytz.UnknownTimeZoneError:
            logger.error(
                f"无效的时区配置: {config.timezone}，请检查 config.timezone 设置。"
            )


async def setup_bot() -> BotClient:
    """初始化并启动 Bot 客户端。"""
    bot_client = BotClient(
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        name="emby_bot",
    )
    await bot_client.start()
    return bot_client


async def fetch_group_members(bot_client: BotClient) -> None:
    """获取群组成员并更新配置。"""
    members_in_group = await bot_client.get_group_members(config.telegram_group_ids)
    for group_members in members_in_group.values():
        for telegram_id in group_members:
            config.group_members[telegram_id] = group_members[telegram_id]


async def main() -> None:
    """主函数，初始化并运行 Bot。"""
    _init_logger()
    _init_tz()

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"程序启动时间: {now}")

    await _init_db()
    logger.info("数据库初始化完成。")

    # 初始化 Bot 客户端
    bot_client = await setup_bot()
    logger.info("Bot 客户端初始化完成。")

    # 初始化 Emby API 和命令处理器
    emby_api = EmbyApi(config.emby_url, config.emby_api)
    emby_router_api = EmbyRouterAPI(config.api_url, config.api_key)
    command_handler = CommandHandler(
        bot_client=bot_client,
        user_service=UserService(emby_api=emby_api, emby_router_api=emby_router_api),
    )
    logger.info("Emby API 和命令处理器初始化完成。")

    try:
        # 获取群组成员
        await fetch_group_members(bot_client)
        logger.info("群组成员信息已更新。")

        # 设置命令并进入空闲状态
        command_handler.setup_commands()
        logger.info("命令处理器设置完成，Bot 进入运行状态。")
        await bot_client.idle()

    except Exception as e:
        logger.error(f"启动 Bot 失败: {e}", exc_info=True)
    finally:
        await bot_client.stop()
        logger.info("Bot 已停止。")


if __name__ == "__main__":
    asyncio.run(main())
    logger.info("bot stop")
