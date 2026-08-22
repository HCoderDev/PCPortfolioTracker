from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from app.services.transaction_type_registry import TransactionTypeRegistry

class CategoryRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("SELECT * FROM ZCATEGORY ORDER BY ZNAME ASC;").fetchall()
        return [CategoryRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_id(cat_id: int):
        db = get_db()
        row = db.execute("SELECT * FROM ZCATEGORY WHERE Z_PK = ?;", (cat_id,)).fetchone()
        return CategoryRepository._map_row(row) if row else None

    @staticmethod
    def get_subcategories(cat_id: int):
        db = get_db()
        rows = db.execute("SELECT * FROM ZSUBCATEGORY WHERE ZCATEGORY = ? ORDER BY ZNAME ASC;", (cat_id,)).fetchall()
        return [{'id': r['Z_PK'], 'category_id': r['ZCATEGORY'], 'name': r['ZNAME']} for r in rows]

    @staticmethod
    def create(data: dict) -> int:
        db = get_db()
        new_pk = get_next_pk("Category")
        last_updated_ts = datetime_to_core_data_timestamp(data['last_updated_date']) if data.get('last_updated_date') else None
        db.execute("""
            INSERT INTO ZCATEGORY (
                Z_PK, Z_ENT, Z_OPT, ZNAME, ZCURRENCYCODE, ZLASTINREXCHANGERATE,
                ZCONVERTTOINR, ZISINDIVIDUALEQUITY, ZTARGETALLOCATION, ZLTCGTHRESHOLDMONTHS,
                ZPASSIVETRANSACTIONTYPESRAW, ZLASTUPDATEDDATE
            ) VALUES (?, 3, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            new_pk,
            data.get('name'),
            data.get('currency_code', 'INR'),
            data.get('last_inr_exchange_rate', 1.0),
            1 if data.get('convert_to_inr', True) else 0,
            1 if data.get('is_individual_equity', False) else 0,
            data.get('target_allocation', 0.0),
            data.get('ltcg_threshold_months', 12),
            data.get('passive_transaction_types_raw', ''),
            last_updated_ts
        ))
        db.commit()
        return new_pk

    @staticmethod
    def update(cat_id: int, data: dict):
        db = get_db()
        last_updated_ts = datetime_to_core_data_timestamp(data['last_updated_date']) if data.get('last_updated_date') else None
        db.execute("""
            UPDATE ZCATEGORY SET
                ZNAME = ?, ZCURRENCYCODE = ?, ZLASTINREXCHANGERATE = ?,
                ZCONVERTTOINR = ?, ZISINDIVIDUALEQUITY = ?, ZTARGETALLOCATION = ?,
                ZLTCGTHRESHOLDMONTHS = ?, ZPASSIVETRANSACTIONTYPESRAW = ?, ZLASTUPDATEDDATE = ?
            WHERE Z_PK = ?;
        """, (
            data.get('name'),
            data.get('currency_code', 'INR'),
            data.get('last_inr_exchange_rate', 1.0),
            1 if data.get('convert_to_inr', True) else 0,
            1 if data.get('is_individual_equity', False) else 0,
            data.get('target_allocation', 0.0),
            data.get('ltcg_threshold_months', 12),
            data.get('passive_transaction_types_raw', ''),
            last_updated_ts,
            cat_id
        ))
        db.commit()

    @staticmethod
    def delete(cat_id: int):
        db = get_db()
        db.execute("DELETE FROM ZSUBCATEGORY WHERE ZCATEGORY = ?;", (cat_id,))
        db.execute("DELETE FROM ZCATEGORY WHERE Z_PK = ?;", (cat_id,))
        db.commit()

    @staticmethod
    def create_subcategory(category_id: int, name: str) -> int:
        db = get_db()
        new_pk = get_next_pk("SubCategory")
        db.execute("INSERT INTO ZSUBCATEGORY (Z_PK, Z_ENT, Z_OPT, ZCATEGORY, ZNAME) VALUES (?, 8, 1, ?, ?);", (new_pk, category_id, name))
        db.commit()
        return new_pk

    @staticmethod
    def delete_subcategory(subcategory_id: int):
        db = get_db()
        db.execute("DELETE FROM ZSUBCATEGORY WHERE Z_PK = ?;", (subcategory_id,))
        db.commit()

    @staticmethod
    def allowed_passive_transaction_types(cat_id: int, cat_name: str = '') -> list:
        db = get_db()
        rows = db.execute("SELECT ZHOLDINGTYPERAW FROM ZASSET WHERE ZCATEGORY = ?;", (cat_id,)).fetchall()
        holding_types = set([r['ZHOLDINGTYPERAW'] for r in rows if r['ZHOLDINGTYPERAW']])

        if not holding_types:
            lower_name = (cat_name or '').lower()
            if 'epf' in lower_name or 'provident' in lower_name:
                holding_types.add('epf')
            elif 'lic' in lower_name or 'insurance' in lower_name or 'policy' in lower_name or 'annuity' in lower_name:
                holding_types.add('insuranceAnnuity')
            elif 'fd' in lower_name or 'fixed deposit' in lower_name or 'rd' in lower_name:
                holding_types.add('fixedDeposit')
            elif 'post office' in lower_name or 'ppf' in lower_name or 'nsc' in lower_name:
                holding_types.add('postOffice')
            else:
                holding_types.add('investment')

        result = []
        for h_type in holding_types:
            config = TransactionTypeRegistry.get_config_for_holding_type(h_type)
            for tx_cfg in config['allowed_transactions']:
                raw = tx_cfg['raw_type'].upper()
                if raw in ['BUY', 'SELL', 'DEPOSIT', 'WITHDRAWAL', 'CONTRIBUTION', 'EMPLOYEE_CONTRIBUTION', 'EMPLOYER_CONTRIBUTION', 'MATURITY', 'SURRENDER', 'PREMIUM']:
                    continue
                if tx_cfg.get('affects_profit') or any(k in raw for k in ['DIVIDEND', 'INTEREST', 'BONUS', 'SURVIVAL', 'COUPON', 'RENT', 'ROYALTY']):
                    if not any(r['id'] == raw for r in result):
                        result.append({'id': raw, 'name': tx_cfg['display_name'], 'icon': tx_cfg['icon_name']})

        # Also check existing transactions in this category for extra types
        tx_rows = db.execute("""
            SELECT DISTINCT ZTYPE, ZRAWTYPERAW FROM ZASSETTRANSACTION 
            JOIN ZASSET ON ZASSETTRANSACTION.ZASSET = ZASSET.Z_PK 
            WHERE ZASSET.ZCATEGORY = ?;
        """, (cat_id,)).fetchall()

        for r in tx_rows:
            raw = (r['ZRAWTYPERAW'] or r['ZTYPE'] or '').upper()
            if any(k in raw for k in ['EMPLOYER', 'EMPLOYEE', 'BUY', 'SELL', 'CONTRIBUTION', 'DEPOSIT', 'MATURITY', 'PREMIUM']):
                continue
            if any(k in raw for k in ['DIVIDEND', 'INTEREST', 'BONUS', 'SURVIVAL', 'COUPON', 'RENT', 'ROYALTY']) and not any(res['id'] == raw for res in result):
                result.append({'id': raw, 'name': raw.title(), 'icon': 'fa-solid fa-tag'})

        if not result:
            result.append({'id': 'DIVIDEND', 'name': 'Dividend Received', 'icon': 'fa-solid fa-gift'})

        return result

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        passive_types_raw = d.get('ZPASSIVETRANSACTIONTYPESRAW') or ''
        passive_types = set([p.strip().upper() for p in passive_types_raw.split('|||') if p.strip()]) if passive_types_raw else set()

        last_updated_date = core_data_timestamp_to_datetime(d.get('ZLASTUPDATEDDATE')) if d.get('ZLASTUPDATEDDATE') is not None else None

        return {
            'id': d['Z_PK'],
            'name': d.get('ZNAME', ''),
            'currency_code': d.get('ZCURRENCYCODE', 'INR'),
            'last_inr_exchange_rate': d.get('ZLASTINREXCHANGERATE', 1.0) or 1.0,
            'convert_to_inr': bool(d.get('ZCONVERTTOINR', True)),
            'is_individual_equity': bool(d.get('ZISINDIVIDUALEQUITY', False)),
            'target_allocation': d.get('ZTARGETALLOCATION', 0.0) or 0.0,
            'ltcg_threshold_months': d.get('ZLTCGTHRESHOLDMONTHS', 12) or 12,
            'passive_transaction_types_raw': passive_types_raw,
            'passive_transaction_types': passive_types,
            'last_updated_date': last_updated_date
        }
