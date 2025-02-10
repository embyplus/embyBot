import logging
from datetime import datetime

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