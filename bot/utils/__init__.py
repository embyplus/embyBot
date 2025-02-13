import functools
import logging
from datetime import datetime

from pyrogram.enums import ParseMode
from pyrogram.types import Message

logger = logging.getLogger(__name__)


def parse_iso8601(datetime_str: str):
    # 解析字符串为 datetime 对象
    try:
        dt = datetime.strptime(
            datetime_str[:26], "%Y-%m-%dT%H:%M:%S.%f"
        )  # 截取到微秒部分
        logger.debug(f"Parsed ISO8601 datetime string: {datetime_str}")
        return dt
    except Exception as e:
        logger.error(
            f"Error parsing ISO8601 datetime string: {datetime_str}: {e}",
            exc_info=True
        )
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
        logger.error(f"Error parsing timestamp {timestamp}: {e}",
                     exc_info=True)
        return None


async def reply_html(message: Message, text: str, **kwargs):
    """
    统一回复方法，使用 HTML parse_mode。
    """
    return await message.reply(text, parse_mode=ParseMode.HTML, **kwargs)


def with_parsed_args(func):
    """
    用于自动解析消息文本参数的装饰器 喵～。
    这个装饰器会从消息的文本中提取以空格分割的参数（除第一个命令外），
    并将解析后的参数列表传递给被装饰的函数 喵～
    """

    @functools.wraps(func)
    async def wrapper(self, message: Message, *args, **kwargs):
        parts = message.text.strip().split(" ")
        parsed_args = parts[1:] if len(parts) > 1 else []
        return await func(self, message, parsed_args, *args, **kwargs)

    return wrapper


def with_ensure_args(min_len: int, usage: str):
    """
    用于确保命令参数数量足够的装饰器 喵～。
    如果传入的参数数量少于要求的最小值，则自动回复提示信息，并终止函数的执行 喵～
    参数：
      min_len - 所需最小参数数量
      usage   - 命令的正确用法示例
    """

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # 判断是否为方法：
            # 如果第一个参数是 Message，则视为普通函数，否则视为类方法（第一个参数为 self）
            if args and isinstance(args[0], Message):
                message_obj = args[0]
                command_args = args[1]
            else:
                message_obj = args[1]
                command_args = args[2]
            if len(command_args) < min_len:
                await reply_html(message_obj,
                                 f"参数不足，请参考用法：\n<code>{usage}</code>")
                return
            return await func(*args, **kwargs)

        return wrapper

    return decorator


async def send_error(message: Message, error: Exception,
                     prefix: str = "操作失败"):
    """
    统一的异常捕获后回复方式。
    """
    logger.error(f"{prefix}：{error}", exc_info=True)
    await reply_html(message, f"{prefix}：{error}")
