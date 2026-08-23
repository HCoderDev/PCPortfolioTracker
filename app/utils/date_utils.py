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

def format_date(dt, fmt: str = "%d-%m-%Y") -> str:
    if dt is None or dt == "":
        return ""
    if isinstance(dt, str):
        parsed = parse_iso_date(dt)
        return parsed.strftime(fmt) if parsed else dt
    if isinstance(dt, (datetime, date)):
        return dt.strftime(fmt)
    return str(dt)

def parse_iso_date(date_str) -> datetime:
    if not date_str:
        return datetime.now(timezone.utc)
    if isinstance(date_str, datetime):
        if date_str.tzinfo is None:
            return date_str.replace(tzinfo=timezone.utc)
        return date_str
    if isinstance(date_str, date):
        return datetime(date_str.year, date_str.month, date_str.day, tzinfo=timezone.utc)
    
    date_str_clean = str(date_str).strip()
    if not date_str_clean:
        return datetime.now(timezone.utc)

    # Try various date formats, prioritizing dd-mm-yyyy and YYYY-MM-DD
    formats = ["%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"]
    
    if "T" in date_str_clean:
        try:
            dt = datetime.fromisoformat(date_str_clean)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            pass

    for fmt in formats:
        try:
            dt = datetime.strptime(date_str_clean, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass

    try:
        dt = datetime.fromisoformat(date_str_clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return datetime.now(timezone.utc)
