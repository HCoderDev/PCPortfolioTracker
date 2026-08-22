from app.db import get_db, get_next_pk

class CurrencyRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("SELECT * FROM ZCURRENCY ORDER BY ZCODE ASC;").fetchall()
        return [CurrencyRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_code(code: str):
        db = get_db()
        row = db.execute("SELECT * FROM ZCURRENCY WHERE UPPER(ZCODE) = UPPER(?);", (code,)).fetchone()
        return CurrencyRepository._map_row(row) if row else None

    @staticmethod
    def get_default():
        db = get_db()
        row = db.execute("SELECT * FROM ZCURRENCY WHERE ZISDEFAULT = 1 LIMIT 1;").fetchone()
        return CurrencyRepository._map_row(row) if row else CurrencyRepository.get_by_code("INR")

    @staticmethod
    def create(code: str, exchange_rate: float, is_default: bool = False) -> int:
        db = get_db()
        new_pk = get_next_pk("Currency")
        if is_default:
            db.execute("UPDATE ZCURRENCY SET ZISDEFAULT = 0;")
        db.execute("""
            INSERT INTO ZCURRENCY (Z_PK, Z_ENT, Z_OPT, ZCODE, ZEXCHANGERATE, ZISDEFAULT)
            VALUES (?, 4, 1, ?, ?, ?);
        """, (new_pk, code.upper(), exchange_rate, 1 if is_default else 0))
        db.commit()
        return new_pk

    @staticmethod
    def update(curr_id: int, exchange_rate: float, is_default: bool = False):
        db = get_db()
        if is_default:
            db.execute("UPDATE ZCURRENCY SET ZISDEFAULT = 0;")
        db.execute("UPDATE ZCURRENCY SET ZEXCHANGERATE = ?, ZISDEFAULT = ? WHERE Z_PK = ?;",
                   (exchange_rate, 1 if is_default else 0, curr_id))
        db.commit()

    @staticmethod
    def delete(curr_id: int):
        db = get_db()
        db.execute("DELETE FROM ZCURRENCY WHERE Z_PK = ?;", (curr_id,))
        db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'code': d.get('ZCODE', ''),
            'exchange_rate': d.get('ZEXCHANGERATE', 1.0) or 1.0,
            'is_default': bool(d.get('ZISDEFAULT', False))
        }
