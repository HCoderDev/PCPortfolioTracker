from app.db import get_db, get_next_pk

class BrokerRepository:
    @staticmethod
    def get_all():
        db = get_db()
        rows = db.execute("SELECT * FROM ZBROKER ORDER BY ZNAME ASC;").fetchall()
        return [BrokerRepository._map_row(r) for r in rows]

    @staticmethod
    def get_by_id(broker_id: int):
        db = get_db()
        row = db.execute("SELECT * FROM ZBROKER WHERE Z_PK = ?;", (broker_id,)).fetchone()
        return BrokerRepository._map_row(row) if row else None

    @staticmethod
    def create(name: str) -> int:
        db = get_db()
        new_pk = get_next_pk("Broker")
        db.execute("INSERT INTO ZBROKER (Z_PK, Z_ENT, Z_OPT, ZNAME) VALUES (?, 2, 1, ?);", (new_pk, name))
        db.commit()
        return new_pk

    @staticmethod
    def update(broker_id: int, name: str):
        db = get_db()
        db.execute("UPDATE ZBROKER SET ZNAME = ? WHERE Z_PK = ?;", (name, broker_id))
        db.commit()

    @staticmethod
    def delete(broker_id: int):
        db = get_db()
        db.execute("DELETE FROM ZBROKER WHERE Z_PK = ?;", (broker_id,))
        db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'name': d.get('ZNAME', '')
        }
