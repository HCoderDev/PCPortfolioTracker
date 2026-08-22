from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from datetime import datetime, timezone

class NoteRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("""
            SELECT n.*, a.ZNAME as asset_name
            FROM ZASSETNOTE n
            LEFT JOIN ZASSET a ON n.ZASSET = a.Z_PK
            ORDER BY n.ZDATE DESC, n.ZCREATEDAT DESC;
        """).fetchall()
        return [NoteRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_asset(asset_id: int):
        db = get_db()
        rows = db.execute("""
            SELECT n.*, a.ZNAME as asset_name
            FROM ZASSETNOTE n
            LEFT JOIN ZASSET a ON n.ZASSET = a.Z_PK
            WHERE n.ZASSET = ?
            ORDER BY n.ZDATE DESC, n.ZCREATEDAT DESC;
        """, (asset_id,)).fetchall()
        return [NoteRepository._map_row(r) for r in rows]

    @staticmethod
    def create(data: dict) -> int:
        db = get_db()
        new_pk = get_next_pk("AssetNote")
        note_dt = data.get('date') or datetime.now(timezone.utc)
        created_dt = data.get('created_at') or datetime.now(timezone.utc)

        db.execute("""
            INSERT INTO ZASSETNOTE (
                Z_PK, Z_ENT, Z_OPT, ZASSET, ZTITLE, ZNOTEDESCRIPTION, ZDATE, ZCREATEDAT
            ) VALUES (?, 7, 1, ?, ?, ?, ?, ?);
        """, (
            new_pk,
            data.get('asset_id'),
            data.get('title', ''),
            data.get('description', ''),
            datetime_to_core_data_timestamp(note_dt),
            datetime_to_core_data_timestamp(created_dt)
        ))
        db.commit()
        return new_pk

    @staticmethod
    def delete(note_id: int):
        db = get_db()
        db.execute("DELETE FROM ZASSETNOTE WHERE Z_PK = ?;", (note_id,))
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
            'description': d.get('ZNOTEDESCRIPTION') or '',
            'date': core_data_timestamp_to_datetime(d.get('ZDATE')),
            'created_at': core_data_timestamp_to_datetime(d.get('ZCREATEDAT'))
        }
