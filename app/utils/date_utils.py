from datetime import datetime, timezone, date
import math

CORE_DATA_EPOCH_OFFSET = 978307200.0  # Seconds between 1970-01-01 and 2001-01-01 UTC

def datetime_to_core_data_timestamp(dt: datetime) -> float:
    if dt is None:
        return 0.0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp() - CORE_DATA_EPOCH_OFFSET

def core_data_timestamp_to_datetime(ts: float) -> datetime:
    if ts is None:
        return datetime.now(timezone.utc)
    unix_ts = float(ts) + CORE_DATA_EPOCH_OFFSET
    return datetime.fromtimestamp(unix_ts, tz=timezone.utc)

def format_date(dt: datetime, fmt: str = "%d %b %Y") -> str:
    if dt is None:
        return ""
    return dt.strftime(fmt)

def parse_iso_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str)
        else:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)
