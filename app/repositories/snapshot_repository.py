from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from datetime import datetime, timezone

class SnapshotRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("SELECT * FROM ZPORTFOLIOSNAPSHOT ORDER BY ZDATE DESC;").fetchall()
        return [SnapshotRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_id(snapshot_id: int):
        db = get_db()
        row = db.execute("SELECT * FROM ZPORTFOLIOSNAPSHOT WHERE Z_PK = ?;", (snapshot_id,)).fetchone()
        if not row: return None
        snap = SnapshotRepository._map_row(row)

        cat_rows = db.execute("SELECT * FROM ZCATEGORYSNAPSHOT WHERE ZPORTFOLIOSNAPSHOT = ?;", (snapshot_id,)).fetchall()
        categories = []
        for cr in cat_rows:
            cat_d = dict(cr)
            asset_rows = db.execute("SELECT * FROM ZASSETSNAPSHOT WHERE ZCATEGORYSNAPSHOT = ?;", (cat_d['Z_PK'],)).fetchall()
            assets = [dict(ar) for ar in asset_rows]
            categories.append({
                'id': cat_d['Z_PK'],
                'category_name': cat_d.get('ZCATEGORYNAME'),
                'currency_code': cat_d.get('ZCURRENCYCODE'),
                'invested_value': cat_d.get('ZINVESTEDVALUE', 0.0),
                'current_value': cat_d.get('ZCURRENTVALUE', 0.0),
                'invested_value_inr': cat_d.get('ZINVESTEDVALUEINR', 0.0),
                'current_value_inr': cat_d.get('ZCURRENTVALUEINR', 0.0),
                'exchange_rate_to_inr': cat_d.get('ZEXCHANGERATETOINR', 1.0),
                'assets': [{
                    'id': a['Z_PK'],
                    'asset_name': a.get('ZASSETNAME'),
                    'units': a.get('ZUNITS', 0.0),
                    'current_price': a.get('ZCURRENTPRICE', 0.0),
                    'invested_value': a.get('ZINVESTEDVALUE', 0.0),
                    'current_value': a.get('ZCURRENTVALUE', 0.0),
                    'invested_value_inr': a.get('ZINVESTEDVALUEINR', 0.0),
                    'current_value_inr': a.get('ZCURRENTVALUEINR', 0.0)
                } for a in assets]
            })
        snap['categories'] = categories
        return snap

    @staticmethod
    def create_snapshot(note: str, total_invested_inr: float, total_value_inr: float, category_data_list: list) -> int:
        db = get_db()
        snap_pk = get_next_pk("PortfolioSnapshot")
        now_ts = datetime_to_core_data_timestamp(datetime.now(timezone.utc))

        db.execute("""
            INSERT INTO ZPORTFOLIOSNAPSHOT (Z_PK, Z_ENT, Z_OPT, ZDATE, ZTOTALINVESTEDINR, ZTOTALVALUEINR, ZNOTE)
            VALUES (?, 12, 1, ?, ?, ?, ?);
        """, (snap_pk, now_ts, total_invested_inr, total_value_inr, note))

        for cat_data in category_data_list:
            cat_pk = get_next_pk("CategorySnapshot")
            db.execute("""
                INSERT INTO ZCATEGORYSNAPSHOT (
                    Z_PK, Z_ENT, Z_OPT, ZPORTFOLIOSNAPSHOT, ZCATEGORYNAME, ZCURRENCYCODE,
                    ZINVESTEDVALUE, ZCURRENTVALUE, ZINVESTEDVALUEINR, ZCURRENTVALUEINR, ZEXCHANGERATETOINR
                ) VALUES (?, 13, 1, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                cat_pk, snap_pk,
                cat_data.get('category_name'), cat_data.get('currency_code', 'INR'),
                cat_data.get('invested_value', 0.0), cat_data.get('current_value', 0.0),
                cat_data.get('invested_value_inr', 0.0), cat_data.get('current_value_inr', 0.0),
                cat_data.get('exchange_rate_to_inr', 1.0)
            ))

            for asset_data in cat_data.get('assets', []):
                asset_pk = get_next_pk("AssetSnapshot")
                db.execute("""
                    INSERT INTO ZASSETSNAPSHOT (
                        Z_PK, Z_ENT, Z_OPT, ZCATEGORYSNAPSHOT, ZASSETNAME, ZUNITS, ZCURRENTPRICE,
                        ZINVESTEDVALUE, ZCURRENTVALUE, ZINVESTEDVALUEINR, ZCURRENTVALUEINR
                    ) VALUES (?, 14, 1, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    asset_pk, cat_pk,
                    asset_data.get('asset_name'), asset_data.get('units', 0.0), asset_data.get('current_price', 0.0),
                    asset_data.get('invested_value', 0.0), asset_data.get('current_value', 0.0),
                    asset_data.get('invested_value_inr', 0.0), asset_data.get('current_value_inr', 0.0)
                ))

        db.commit()
        return snap_pk

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'date': core_data_timestamp_to_datetime(d.get('ZDATE')),
            'total_invested_inr': d.get('ZTOTALINVESTEDINR', 0.0) or 0.0,
            'total_value_inr': d.get('ZTOTALVALUEINR', 0.0) or 0.0,
            'note': d.get('ZNOTE') or ''
        }
