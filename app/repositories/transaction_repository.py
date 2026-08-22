from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from datetime import datetime, timezone

class TransactionRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("""
            SELECT t.*, a.ZNAME as asset_name, c.ZNAME as category_name, c.ZCURRENCYCODE as currency_code,
                   c.Z_PK as category_id, b.ZNAME as broker_name, a.ZHOLDINGTYPERAW as asset_holding_type
            FROM ZASSETTRANSACTION t
            LEFT JOIN ZASSET a ON t.ZASSET = a.Z_PK
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZBROKER b ON t.ZBROKER = b.Z_PK
            ORDER BY t.ZDATE DESC, t.ZCREATEDAT DESC;
        """).fetchall()
        return [TransactionRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_asset(asset_id: int):
        db = get_db()
        rows = db.execute("""
            SELECT t.*, a.ZNAME as asset_name, c.ZNAME as category_name, c.ZCURRENCYCODE as currency_code,
                   c.Z_PK as category_id, b.ZNAME as broker_name, a.ZHOLDINGTYPERAW as asset_holding_type
            FROM ZASSETTRANSACTION t
            LEFT JOIN ZASSET a ON t.ZASSET = a.Z_PK
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZBROKER b ON t.ZBROKER = b.Z_PK
            WHERE t.ZASSET = ?
            ORDER BY t.ZDATE DESC, t.ZCREATEDAT DESC;
        """, (asset_id,)).fetchall()
        return [TransactionRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_id(tx_id: int):
        db = get_db()
        row = db.execute("""
            SELECT t.*, a.ZNAME as asset_name, c.ZNAME as category_name, c.ZCURRENCYCODE as currency_code,
                   c.Z_PK as category_id, b.ZNAME as broker_name, a.ZHOLDINGTYPERAW as asset_holding_type
            FROM ZASSETTRANSACTION t
            LEFT JOIN ZASSET a ON t.ZASSET = a.Z_PK
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZBROKER b ON t.ZBROKER = b.Z_PK
            WHERE t.Z_PK = ?;
        """, (tx_id,)).fetchone()
        return TransactionRepository._map_row(row) if row else None

    @staticmethod
    def create(data: dict) -> int:
        db = get_db()
        new_pk = get_next_pk("AssetTransaction")
        tx_date = data.get('date') or datetime.now(timezone.utc)
        created_at = data.get('created_at') or datetime.now(timezone.utc)
        
        date_ts = datetime_to_core_data_timestamp(tx_date)
        created_ts = datetime_to_core_data_timestamp(created_at)

        db.execute("""
            INSERT INTO ZASSETTRANSACTION (
                Z_PK, Z_ENT, Z_OPT, ZASSET, ZBROKER, ZTYPE, ZRAWTYPERAW,
                ZUNITS, ZPRICEPERUNIT, ZDATE, ZCREATEDAT, ZINREXCHANGERATE, ZNOTES
            ) VALUES (?, 6, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            new_pk,
            data.get('asset_id'),
            data.get('broker_id'),
            data.get('type', 'BUY').upper(),
            data.get('raw_type', data.get('type', 'BUY')).upper(),
            data.get('units', 0.0),
            data.get('price_per_unit', 0.0),
            date_ts,
            created_ts,
            data.get('inr_exchange_rate'),
            data.get('notes', '')
        ))
        db.commit()
        return new_pk

    @staticmethod
    def update(tx_id: int, data: dict):
        db = get_db()
        tx_date = data.get('date') or datetime.now(timezone.utc)
        date_ts = datetime_to_core_data_timestamp(tx_date)

        db.execute("""
            UPDATE ZASSETTRANSACTION SET
                ZASSET = ?, ZBROKER = ?, ZTYPE = ?, ZRAWTYPERAW = ?,
                ZUNITS = ?, ZPRICEPERUNIT = ?, ZDATE = ?, ZINREXCHANGERATE = ?, ZNOTES = ?
            WHERE Z_PK = ?;
        """, (
            data.get('asset_id'),
            data.get('broker_id'),
            data.get('type', 'BUY').upper(),
            data.get('raw_type', data.get('type', 'BUY')).upper(),
            data.get('units', 0.0),
            data.get('price_per_unit', 0.0),
            date_ts,
            data.get('inr_exchange_rate'),
            data.get('notes', ''),
            tx_id
        ))
        db.commit()

    @staticmethod
    def update_exchange_rate(tx_id: int, rate: float):
        db = get_db()
        db.execute("UPDATE ZASSETTRANSACTION SET ZINREXCHANGERATE = ? WHERE Z_PK = ?;", (rate, tx_id))
        db.commit()

    @staticmethod
    def delete(tx_id: int):
        db = get_db()
        db.execute("DELETE FROM ZASSETTRANSACTION WHERE Z_PK = ?;", (tx_id,))
        db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        tx_date = core_data_timestamp_to_datetime(d.get('ZDATE'))
        created_at = core_data_timestamp_to_datetime(d.get('ZCREATEDAT'))
        raw_type = d.get('ZRAWTYPERAW') or d.get('ZTYPE', 'BUY')

        return {
            'id': d['Z_PK'],
            'asset_id': d.get('ZASSET'),
            'asset_name': d.get('asset_name', ''),
            'category_id': d.get('category_id'),
            'category_name': d.get('category_name', ''),
            'currency_code': d.get('currency_code', 'INR'),
            'broker_id': d.get('ZBROKER'),
            'broker_name': d.get('broker_name', ''),
            'type': d.get('ZTYPE', 'BUY').upper(),
            'raw_type': raw_type.upper(),
            'units': d.get('ZUNITS', 0.0) or 0.0,
            'price_per_unit': d.get('ZPRICEPERUNIT', 0.0) or 0.0,
            'date': tx_date,
            'created_at': created_at,
            'inr_exchange_rate': d.get('ZINREXCHANGERATE'),
            'notes': d.get('ZNOTES') or '',
            'asset_holding_type': d.get('asset_holding_type', 'investment')
        }
