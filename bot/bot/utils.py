from datetime import datetime


def parse_iso8601(datetime_str: str):
    # 解析字符串为 datetime 对象
    dt = datetime.strptime(datetime_str[:26], "%Y-%m-%dT%H:%M:%S.%f")  # 截取到微秒部分
    return dt


def parse_iso8601_to_timestamp(datetime_str: str):
    dt = parse_iso8601(datetime_str)
    return dt.timestamp()


def parse_iso8601_to_normal_date(datetime_str: str):
    dt = parse_iso8601(datetime_str)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def parse_timestamp_to_normal_date(timestamp: int):
    dt = datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")
