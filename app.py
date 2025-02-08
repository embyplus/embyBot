import asyncio
import logging
from datetime import datetime

import pytz
from py_tools.connections.db.mysql import DBManager, BaseOrmTable, SQLAlchemyManager

from bot.bot_client import BotClient
from bot.commands import CommandHandler
from config import config
from core.emby_api import EmbyApi, EmbyRouterAPI
from services import UserService

logger = logging.getLogger(__name__)


async def init_db():
    """
    初始化数据库连接并创建表。
    """
    db_client = SQLAlchemyManager(
        host=config.db_host,
        port=config.db_port,
        user=config.db_user,
        password=config.db_pass,
        db_name=config.db_name,
    )
    db_client.init_mysql_engine()
    DBManager.init_db_client(db_client)
    async with DBManager.connection() as conn:
        await conn.run_sync(BaseOrmTable.metadata.create_all)
    logger.info("Database initialized successfully.")


def init_logger():
    """
    初始化日志配置。
    """
    logging.basicConfig(
        format="%(levelname)s [%(asctime)s] %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        level=config.log_level,
        filename="default.log",
    )
    logger.info("Logger initialized successfully.")


def init_timezone():
    """
    初始化时区配置。
    """
    if config.timezone:
        pytz.timezone(config.timezone)
        logger.info(f"Timezone set to: {config.timezone}")


async def fetch_group_members(bot_client: BotClient):
    """
    获取群组成员并更新配置。
    """
    members_in_group = await bot_client.get_group_members(config.telegram_group_ids)
    for group_members in members_in_group.values():
        for telegram_id in group_members:
            config.group_members[telegram_id] = group_members[telegram_id]
    logger.info("Group members fetched and updated in config.")


async def main():
    """
    主函数，初始化并启动 Bot 客户端。
    """
    logger.info("Starting application...")
    logger.info(f"Current time: {datetime.now()}")

    # 初始化配置
    init_timezone()
    init_logger()
    await init_db()

    # 创建 Bot 客户端
    bot_client = BotClient(
        api_id=config.api_id,
        api_hash=config.api_hash,
        bot_token=config.bot_token,
        name="emby_bot",
    )
    emby_api = EmbyApi(config.emby_url, config.emby_api)
    emby_router_api = EmbyRouterAPI(config.api_url, config.api_key)

    # 设置命令处理
    command_handler = CommandHandler(
        bot_client=bot_client,
        user_service=UserService(
            emby_api=emby_api,
            emby_router_api=emby_router_api
        )
    )

    try:
        await bot_client.start()
        logger.info("Bot client started successfully.")

        # 获取群组成员
        await fetch_group_members(bot_client)

        # 设置命令并进入空闲状态
        command_handler.setup_commands()
        logger.info("Command handler setup completed.")
        await bot_client.idle()

    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        await bot_client.stop()
        logger.info("Bot client stopped due to an error.")
    finally:
        logger.info("Application shutdown completed.")


if __name__ == "__main__":
    asyncio.run(main())
