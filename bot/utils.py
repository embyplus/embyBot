import logging
from datetime import datetime

from pyrogram.enums import ParseMode
from pyrogram.types import Message

logger = logging.getLogger(__name__)


def parse_iso8601(datetime_str: str):
    # 解析字符串为 datetime 对象
    try:
        dt = datetime.strptime(datetime_str[:26], "%Y-%m-%dT%H:%M:%S.%f")  # 截取到微秒部分
        logger.debug(f"Parsed ISO8601 datetime string: {datetime_str}")
        return dt
    except Exception as e:
        logger.error(f"Error parsing ISO8601 datetime string: {datetime_str}: {e}", exc_info=True)
        return None


def parse_iso8601_to_timestamp(datetime_str: str):
    dt = parse_iso8601(datetime_str)
    if dt:
        return dt.timestamp()
    return None


def parse_iso8601_to_normal_date(datetime_str: str):
    dt = parse_iso8601(datetime_str)
    if dt:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return None


def parse_timestamp_to_normal_date(timestamp: int):
    try:
        dt = datetime.fromtimestamp(timestamp)
        logger.debug(f"Parsed timestamp: {timestamp}")
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"Error parsing timestamp {timestamp}: {e}", exc_info=True)
        return None


async def reply_html(message: Message, text: str, **kwargs):
    """
    统一回复方法，使用 HTML parse_mode。
    """
    return await message.reply(text, parse_mode=ParseMode.HTML, **kwargs)


def parse_args(message: Message) -> list[str]:
    """
    将用户输入拆分为命令 + 参数列表，如：
    '/create testuser' -> ['testuser']
    """
    parts = message.text.strip().split(" ")
    return parts[1:] if len(parts) > 1 else []


async def ensure_args(message: Message, args: list, min_len: int, usage: str):
    """
    确保命令行参数长度足够，不足则回复用法说明。
    """
    if len(args) < min_len:
        await reply_html(message, f"参数不足，请参考用法：\n<code>{usage}</code>")
        return False
    return True


async def send_error(message: Message, error: Exception, prefix: str = "操作失败"):
    """
    统一的异常捕获后回复方式。
    """
    logger.error(f"{prefix}：{error}", exc_info=True)
    await reply_html(message, f"{prefix}：{error}")
