from datetime import datetime, timezone, date
from app.utils.date_utils import format_date, parse_iso_date

def test_format_date():
    dt = datetime(2026, 8, 23, 14, 5, tzinfo=timezone.utc)
    assert format_date(dt) == "23-08-2026"
    assert format_date("2026-08-23") == "23-08-2026"
    assert format_date("23-08-2026") == "23-08-2026"
    assert format_date(date(2026, 8, 23)) == "23-08-2026"
    assert format_date(None) == ""
    assert format_date("") == ""

def test_parse_iso_date():
    dt1 = parse_iso_date("23-08-2026")
    assert dt1.day == 23 and dt1.month == 8 and dt1.year == 2026

    dt2 = parse_iso_date("2026-08-23")
    assert dt2.day == 23 and dt2.month == 8 and dt2.year == 2026

    dt3 = parse_iso_date("23/08/2026")
    assert dt3.day == 23 and dt3.month == 8 and dt3.year == 2026

    dt4 = parse_iso_date("2026-08-23T14:05:00")
    assert dt4.day == 23 and dt4.month == 8 and dt4.year == 2026
