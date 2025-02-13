import logging
import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

logger = logging.getLogger(__name__)


class Config:
    def __init__(self):
        self.timezone = os.getenv("TIMEZONE")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.bot_token = os.getenv("BOT_TOKEN")
        self.api_id = os.getenv("API_ID")
        self.api_hash = os.getenv("API_HASH")
        self.telegram_group_ids = list(
            map(int, os.getenv("TELEGRAM_GROUP_ID").split(","))
        )
        self.emby_url = os.getenv("EMBY_URL")
        self.emby_api = os.getenv("EMBY_API_KEY")
        self.api_url = os.getenv("API_URL")
        self.api_key = os.getenv("API_KEY")
        self.db_host = os.getenv("DB_HOST")
        self.db_port = os.getenv("DB_PORT")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")
        self.db_name = os.getenv("DB_NAME")
        # 处理以逗号分隔的管理员列表
        self.admin_list = list(map(int, os.getenv("ADMIN_LIST").split(",")))
        self.router_list = {}
        self.group_members = {}

        logger.info(f"Configuration loaded")


# 实例化并提供配置对象
config = Config()
logger.debug(f"Admin list: {config.admin_list}")
