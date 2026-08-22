from app.db import get_db, get_next_pk

class UserRepository:
    @staticmethod
    def _ensure_birth_date_column():
        db = get_db()
        cols = [r['name'] for r in db.execute("PRAGMA table_info(ZUSER);").fetchall()]
        if 'ZBIRTHDATERAW' not in cols:
            try:
                db.execute("ALTER TABLE ZUSER ADD COLUMN ZBIRTHDATERAW VARCHAR;")
                db.commit()
            except Exception:
                pass

    @staticmethod
    def get_user():
        UserRepository._ensure_birth_date_column()
        db = get_db()
        row = db.execute("SELECT * FROM ZUSER LIMIT 1;").fetchone()
        return UserRepository._map_row(row) if row else None

    @staticmethod
    def create_or_update(username: str, slab_rate: float = 0.30, birth_date: str = None) -> int:
        UserRepository._ensure_birth_date_column()
        db = get_db()
        user = UserRepository.get_user()
        if user:
            if birth_date:
                db.execute("UPDATE ZUSER SET ZUSERNAME = ?, ZTAXSLABRATERAW = ?, ZBIRTHDATERAW = ? WHERE Z_PK = ?;",
                           (username, slab_rate, birth_date, user['id']))
            else:
                db.execute("UPDATE ZUSER SET ZUSERNAME = ?, ZTAXSLABRATERAW = ? WHERE Z_PK = ?;",
                           (username, slab_rate, user['id']))
            db.commit()
            return user['id']
        else:
            new_pk = get_next_pk("User")
            db.execute("INSERT INTO ZUSER (Z_PK, Z_ENT, Z_OPT, ZUSERNAME, ZTAXSLABRATERAW, ZBIRTHDATERAW) VALUES (?, 5, 1, ?, ?, ?);",
                       (new_pk, username, slab_rate, birth_date))
            db.commit()
            return new_pk

    @staticmethod
    def update_birth_date(birth_date: str):
        UserRepository._ensure_birth_date_column()
        user = UserRepository.get_user()
        if user:
            db = get_db()
            db.execute("UPDATE ZUSER SET ZBIRTHDATERAW = ? WHERE Z_PK = ?;", (birth_date, user['id']))
            db.commit()
        else:
            UserRepository.create_or_update(username="Portfolio User", birth_date=birth_date)

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'username': d.get('ZUSERNAME', ''),
            'tax_slab_rate': d.get('ZTAXSLABRATERAW', 0.30) or 0.30,
            'birth_date': d.get('ZBIRTHDATERAW') or None
        }
