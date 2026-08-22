from app.db import get_db, get_next_pk
from app.utils.date_utils import core_data_timestamp_to_datetime, datetime_to_core_data_timestamp
from datetime import datetime, timezone

class AnalysisRepository:
    @staticmethod
    def get_stock_value_analysis(asset_id: int):
        db = get_db()
        row = db.execute("SELECT * FROM ZSTOCKVALUEANALYSIS WHERE ZASSET = ? LIMIT 1;", (asset_id,)).fetchone()
        return AnalysisRepository._map_value_row(row) if row else None

    @staticmethod
    def create_or_update_value_analysis(asset_id: int, data: dict) -> int:
        db = get_db()
        existing = db.execute("SELECT Z_PK FROM ZSTOCKVALUEANALYSIS WHERE ZASSET = ? LIMIT 1;", (asset_id,)).fetchone()
        now_ts = datetime_to_core_data_timestamp(datetime.now(timezone.utc))

        eps_str = data.get('eps_values_string', '')
        dps_str = data.get('dps_values_string', '')

        if existing:
            pk = existing['Z_PK']
            db.execute("""
                UPDATE ZSTOCKVALUEANALYSIS SET
                    ZANALYSISDATE = ?, ZINVESTMENTPERIOD = ?, ZCMP = ?, ZINTRINSICPE = ?, ZINDUSTRYPE = ?,
                    ZBOOKVALUE = ?, ZDEBTTOEQUITY = ?, ZFREECASHFLOW = ?, ZFREECASHFLOWRATIO = ?,
                    ZCONSENSUSGROWTHRATE = ?, ZCONSENSUSDIVPAYOUTRATIO = ?, ZEPSVALUESSTRING = ?,
                    ZDPSVALUESSTRING = ?, ZINDUSTRY = ?, ZBESTCASEPE = ?
                WHERE Z_PK = ?;
            """, (
                now_ts, data.get('investment_period', 5), data.get('cmp', 0.0), data.get('intrinsic_pe', 0.0),
                data.get('industry_pe', 0.0), data.get('book_value', 0.0), data.get('debt_to_equity', 0.0),
                data.get('free_cash_flow', 0.0), data.get('fcf_ratio', 0.0), data.get('consensus_growth_rate', 0.0),
                data.get('consensus_div_payout_ratio', 0.0), eps_str, dps_str, data.get('industry', ''),
                data.get('best_case_pe', 0.0), pk
            ))
            db.commit()
            return pk
        else:
            new_pk = get_next_pk("StockValueAnalysis")
            db.execute("""
                INSERT INTO ZSTOCKVALUEANALYSIS (
                    Z_PK, Z_ENT, Z_OPT, ZASSET, ZANALYSISDATE, ZINVESTMENTPERIOD, ZCMP, ZINTRINSICPE, ZINDUSTRYPE,
                    ZBOOKVALUE, ZDEBTTOEQUITY, ZFREECASHFLOW, ZFREECASHFLOWRATIO, ZCONSENSUSGROWTHRATE,
                    ZCONSENSUSDIVPAYOUTRATIO, ZEPSVALUESSTRING, ZDPSVALUESSTRING, ZINDUSTRY, ZBESTCASEPE
                ) VALUES (?, 9, 1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                new_pk, asset_id, now_ts, data.get('investment_period', 5), data.get('cmp', 0.0),
                data.get('intrinsic_pe', 0.0), data.get('industry_pe', 0.0), data.get('book_value', 0.0),
                data.get('debt_to_equity', 0.0), data.get('free_cash_flow', 0.0), data.get('fcf_ratio', 0.0),
                data.get('consensus_growth_rate', 0.0), data.get('consensus_div_payout_ratio', 0.0),
                eps_str, dps_str, data.get('industry', ''), data.get('best_case_pe', 0.0)
            ))
            db.execute("UPDATE ZASSET SET ZVALUEANALYSIS = ? WHERE Z_PK = ?;", (new_pk, asset_id))
            db.commit()
            return new_pk

    @staticmethod
    def get_stock_dcf_analysis(asset_id: int):
        db = get_db()
        row = db.execute("SELECT * FROM ZSTOCKDCFANALYSIS WHERE ZASSET = ? LIMIT 1;", (asset_id,)).fetchone()
        return AnalysisRepository._map_dcf_row(row) if row else None

    @staticmethod
    def create_or_update_dcf_analysis(asset_id: int, data: dict) -> int:
        db = get_db()
        existing = db.execute("SELECT Z_PK FROM ZSTOCKDCFANALYSIS WHERE ZASSET = ? LIMIT 1;", (asset_id,)).fetchone()
        now_ts = datetime_to_core_data_timestamp(datetime.now(timezone.utc))

        if existing:
            pk = existing['Z_PK']
            db.execute("""
                UPDATE ZSTOCKDCFANALYSIS SET
                    ZANALYSISDATE = ?, ZCMP = ?, ZSTARTINGFCF = ?, ZGROWTHRATE = ?, ZDISCOUNTRATE = ?,
                    ZTERMINALGROWTH = ?, ZSHARES = ?
                WHERE Z_PK = ?;
            """, (
                now_ts, data.get('cmp', 0.0), data.get('starting_fcf', 0.0), data.get('growth_rate', 0.0),
                data.get('discount_rate', 0.0), data.get('terminal_growth', 0.0), data.get('shares', 0.0), pk
            ))
            db.commit()
            return pk
        else:
            new_pk = get_next_pk("StockDCFAnalysis")
            db.execute("""
                INSERT INTO ZSTOCKDCFANALYSIS (
                    Z_PK, Z_ENT, Z_OPT, ZASSET, ZANALYSISDATE, ZCMP, ZSTARTINGFCF, ZGROWTHRATE,
                    ZDISCOUNTRATE, ZTERMINALGROWTH, ZSHARES
                ) VALUES (?, 10, 1, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                new_pk, asset_id, now_ts, data.get('cmp', 0.0), data.get('starting_fcf', 0.0),
                data.get('growth_rate', 0.0), data.get('discount_rate', 0.0), data.get('terminal_growth', 0.0),
                data.get('shares', 0.0)
            ))
            db.execute("UPDATE ZASSET SET ZDCFANALYSIS = ? WHERE Z_PK = ?;", (new_pk, asset_id))
            db.commit()
            return new_pk

    @staticmethod
    def _map_value_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'asset_id': d.get('ZASSET'),
            'analysis_date': core_data_timestamp_to_datetime(d.get('ZANALYSISDATE')),
            'investment_period': d.get('ZINVESTMENTPERIOD', 5),
            'cmp': d.get('ZCMP', 0.0) or 0.0,
            'intrinsic_pe': d.get('ZINTRINSICPE', 0.0) or 0.0,
            'industry_pe': d.get('ZINDUSTRYPE', 0.0) or 0.0,
            'book_value': d.get('ZBOOKVALUE', 0.0) or 0.0,
            'debt_to_equity': d.get('ZDEBTTOEQUITY', 0.0) or 0.0,
            'free_cash_flow': d.get('ZFREECASHFLOW', 0.0) or 0.0,
            'fcf_ratio': d.get('ZFREECASHFLOWRATIO', 0.0) or 0.0,
            'consensus_growth_rate': d.get('ZCONSENSUSGROWTHRATE', 0.0) or 0.0,
            'consensus_div_payout_ratio': d.get('ZCONSENSUSDIVPAYOUTRATIO', 0.0) or 0.0,
            'eps_values_string': d.get('ZEPSVALUESSTRING') or '',
            'dps_values_string': d.get('ZDPSVALUESSTRING') or '',
            'industry': d.get('ZINDUSTRY') or '',
            'best_case_pe': d.get('ZBESTCASEPE', 0.0) or 0.0
        }

    @staticmethod
    def _map_dcf_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'asset_id': d.get('ZASSET'),
            'analysis_date': core_data_timestamp_to_datetime(d.get('ZANALYSISDATE')),
            'cmp': d.get('ZCMP', 0.0) or 0.0,
            'starting_fcf': d.get('ZSTARTINGFCF', 0.0) or 0.0,
            'growth_rate': d.get('ZGROWTHRATE', 0.0) or 0.0,
            'discount_rate': d.get('ZDISCOUNTRATE', 0.0) or 0.0,
            'terminal_growth': d.get('ZTERMINALGROWTH', 0.0) or 0.0,
            'shares': d.get('ZSHARES', 0.0) or 0.0
        }
