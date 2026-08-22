from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from datetime import datetime, timezone

class ReminderRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("""
            SELECT r.*, a.ZNAME as asset_name
            FROM ZASSETREMINDER r
            LEFT JOIN ZASSET a ON r.ZASSET = a.Z_PK
            ORDER BY r.ZEVENTDATE ASC;
        """).fetchall()
        return [ReminderRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_asset(asset_id: int):
        db = get_db()
        rows = db.execute("""
            SELECT r.*, a.ZNAME as asset_name
            FROM ZASSETREMINDER r
            LEFT JOIN ZASSET a ON r.ZASSET = a.Z_PK
            WHERE r.ZASSET = ?
            ORDER BY r.ZEVENTDATE ASC;
        """, (asset_id,)).fetchall()
        return [ReminderRepository._map_row(r) for r in rows]

    @staticmethod
    def create(data: dict) -> int:
        db = get_db()
        new_pk = get_next_pk("AssetReminder")
        event_dt = data.get('event_date') or datetime.now(timezone.utc)
        created_dt = data.get('created_at') or datetime.now(timezone.utc)

        db.execute("""
            INSERT INTO ZASSETREMINDER (
                Z_PK, Z_ENT, Z_OPT, ZASSET, ZTITLE, ZNOTES, ZEVENTDATE, ZISCOMPLETED, ZCREATEDAT
            ) VALUES (?, 11, 1, ?, ?, ?, ?, ?, ?);
        """, (
            new_pk,
            data.get('asset_id'),
            data.get('title', ''),
            data.get('notes', ''),
            datetime_to_core_data_timestamp(event_dt),
            1 if data.get('is_completed') else 0,
            datetime_to_core_data_timestamp(created_dt)
        ))
        db.commit()
        return new_pk

    @staticmethod
    def toggle_complete(reminder_id: int, is_completed: bool):
        db = get_db()
        db.execute("UPDATE ZASSETREMINDER SET ZISCOMPLETED = ? WHERE Z_PK = ?;", (1 if is_completed else 0, reminder_id))
        db.commit()

    @staticmethod
    def delete(reminder_id: int):
        db = get_db()
        db.execute("DELETE FROM ZASSETREMINDER WHERE Z_PK = ?;", (reminder_id,))
        db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'asset_id': d.get('ZASSET'),
            'asset_name': d.get('asset_name', ''),
            'title': d.get('ZTITLE', ''),
            'notes': d.get('ZNOTES') or '',
            'event_date': core_data_timestamp_to_datetime(d.get('ZEVENTDATE')),
            'is_completed': bool(d.get('ZISCOMPLETED')),
            'created_at': core_data_timestamp_to_datetime(d.get('ZCREATEDAT'))
        }
