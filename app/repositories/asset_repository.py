from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp

class AssetRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("""
            SELECT a.*, c.ZNAME as category_name, c.ZCURRENCYCODE as category_currency,
                   sc.ZNAME as subcategory_name
            FROM ZASSET a
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZSUBCATEGORY sc ON a.ZSUBCATEGORY = sc.Z_PK
            ORDER BY a.ZNAME ASC;
        """).fetchall()
        return [AssetRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_id(asset_id: int):
        db = get_db()
        row = db.execute("""
            SELECT a.*, c.ZNAME as category_name, c.ZCURRENCYCODE as category_currency,
                   sc.ZNAME as subcategory_name
            FROM ZASSET a
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZSUBCATEGORY sc ON a.ZSUBCATEGORY = sc.Z_PK
            WHERE a.Z_PK = ?;
        """, (asset_id,)).fetchone()
        return AssetRepository._map_row(row) if row else None

    @staticmethod
    def get_by_category(category_id: int):
        db = get_db()
        rows = db.execute("""
            SELECT a.*, c.ZNAME as category_name, c.ZCURRENCYCODE as category_currency,
                   sc.ZNAME as subcategory_name
            FROM ZASSET a
            LEFT JOIN ZCATEGORY c ON a.ZCATEGORY = c.Z_PK
            LEFT JOIN ZSUBCATEGORY sc ON a.ZSUBCATEGORY = sc.Z_PK
            WHERE a.ZCATEGORY = ?
            ORDER BY a.ZNAME ASC;
        """, (category_id,)).fetchall()
        return [AssetRepository._map_row(r) for r in rows]

    @staticmethod
    def create(data: dict) -> int:
        db = get_db()
        new_pk = get_next_pk("Asset")
        maturity_ts = datetime_to_core_data_timestamp(data.get('maturity_date')) if data.get('maturity_date') else None

        db.execute("""
            INSERT INTO ZASSET (
                Z_PK, Z_ENT, Z_OPT, ZNAME, ZCURRENTPRICE, ZCATEGORY, ZSUBCATEGORY,
                ZTAXCOUNTRYRAW, ZTAXASSETTYPERAW, ZHOLDINGTYPERAW, ZTICKERRAW, ZALIASESRAW,
                ZISCOMPLETEDRAW, ZINTERESTRATERAW, ZPRINCIPALAMOUNTRAW, ZMATURITYDATERAW,
                ZPAYOUTFREQUENCYRAW, ZPREMIUMAMOUNTRAW, ZPREMIUMTERMYEARSRAW, ZPOLICYNUMBERRAW, ZINSTITUTIONNAMERAW
            ) VALUES (?, 1, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            new_pk,
            data.get('name'),
            data.get('current_price', 0.0),
            data.get('category_id'),
            data.get('subcategory_id'),
            data.get('tax_country', 'India'),
            data.get('tax_asset_type', 'equity'),
            data.get('holding_type', 'investment'),
            data.get('ticker', ''),
            data.get('aliases_raw', ''),
            1 if data.get('is_completed') else 0,
            data.get('interest_rate', 0.0),
            data.get('principal_amount', 0.0),
            maturity_ts,
            data.get('payout_frequency', 'cumulative'),
            data.get('premium_amount', 0.0),
            data.get('premium_term_years', 0),
            data.get('policy_number', ''),
            data.get('institution_name', '')
        ))
        db.commit()
        return new_pk

    @staticmethod
    def update(asset_id: int, data: dict):
        db = get_db()
        maturity_ts = datetime_to_core_data_timestamp(data.get('maturity_date')) if data.get('maturity_date') else None

        db.execute("""
            UPDATE ZASSET SET
                ZNAME = ?, ZCURRENTPRICE = ?, ZCATEGORY = ?, ZSUBCATEGORY = ?,
                ZTAXCOUNTRYRAW = ?, ZTAXASSETTYPERAW = ?, ZHOLDINGTYPERAW = ?, ZTICKERRAW = ?,
                ZALIASESRAW = ?, ZISCOMPLETEDRAW = ?, ZINTERESTRATERAW = ?, ZPRINCIPALAMOUNTRAW = ?,
                ZMATURITYDATERAW = ?, ZPAYOUTFREQUENCYRAW = ?, ZPREMIUMAMOUNTRAW = ?,
                ZPREMIUMTERMYEARSRAW = ?, ZPOLICYNUMBERRAW = ?, ZINSTITUTIONNAMERAW = ?
            WHERE Z_PK = ?;
        """, (
            data.get('name'),
            data.get('current_price', 0.0),
            data.get('category_id'),
            data.get('subcategory_id'),
            data.get('tax_country', 'India'),
            data.get('tax_asset_type', 'equity'),
            data.get('holding_type', 'investment'),
            data.get('ticker', ''),
            data.get('aliases_raw', ''),
            1 if data.get('is_completed') else 0,
            data.get('interest_rate', 0.0),
            data.get('principal_amount', 0.0),
            maturity_ts,
            data.get('payout_frequency', 'cumulative'),
            data.get('premium_amount', 0.0),
            data.get('premium_term_years', 0),
            data.get('policy_number', ''),
            data.get('institution_name', ''),
            asset_id
        ))
        db.commit()

    @staticmethod
    def update_price(asset_id: int, current_price: float):
        db = get_db()
        db.execute("UPDATE ZASSET SET ZCURRENTPRICE = ? WHERE Z_PK = ?;", (current_price, asset_id))
        db.commit()

    @staticmethod
    def delete(asset_id: int):
        db = get_db()
        db.execute("DELETE FROM ZASSETTRANSACTION WHERE ZASSET = ?;", (asset_id,))
        db.execute("DELETE FROM ZASSETNOTE WHERE ZASSET = ?;", (asset_id,))
        db.execute("DELETE FROM ZASSETREMINDER WHERE ZASSET = ?;", (asset_id,))
        db.execute("DELETE FROM ZASSET WHERE Z_PK = ?;", (asset_id,))
        db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        maturity_date = core_data_timestamp_to_datetime(d.get('ZMATURITYDATERAW')) if d.get('ZMATURITYDATERAW') is not None else None
        
        # Parse aliases
        raw_aliases = d.get('ZALIASESRAW') or ''
        aliases = [a.strip() for a in raw_aliases.split('|||') if a.strip()] if raw_aliases else []

        return {
            'id': d['Z_PK'],
            'name': d.get('ZNAME', ''),
            'current_price': d.get('ZCURRENTPRICE', 0.0) or 0.0,
            'category_id': d.get('ZCATEGORY'),
            'category_name': d.get('category_name', ''),
            'category_currency': d.get('category_currency', 'INR'),
            'subcategory_id': d.get('ZSUBCATEGORY'),
            'subcategory_name': d.get('subcategory_name', ''),
            'tax_country': d.get('ZTAXCOUNTRYRAW') or ('India' if d.get('category_currency') == 'INR' else 'United States'),
            'tax_asset_type': d.get('ZTAXASSETTYPERAW') or 'equity',
            'holding_type': d.get('ZHOLDINGTYPERAW') or 'investment',
            'ticker': d.get('ZTICKERRAW') or '',
            'aliases_raw': raw_aliases,
            'aliases': aliases,
            'is_completed': bool(d.get('ZISCOMPLETEDRAW')),
            'interest_rate': d.get('ZINTERESTRATERAW') or 0.0,
            'principal_amount': d.get('ZPRINCIPALAMOUNTRAW') or 0.0,
            'maturity_date': maturity_date,
            'payout_frequency': d.get('ZPAYOUTFREQUENCYRAW') or 'cumulative',
            'premium_amount': d.get('ZPREMIUMAMOUNTRAW') or 0.0,
            'premium_term_years': d.get('ZPREMIUMTERMYEARSRAW') or 0,
            'policy_number': d.get('ZPOLICYNUMBERRAW') or '',
            'institution_name': d.get('ZINSTITUTIONNAMERAW') or '',
            'value_analysis_id': d.get('ZVALUEANALYSIS'),
            'dcf_analysis_id': d.get('ZDCFANALYSIS')
        }
