from app.db import get_db, get_next_pk

class UserRepository:
    @staticmethod
    def _ensure_fi_columns():
        db = get_db()
        try:
            tbl_check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ZUSER';").fetchone()
            if not tbl_check:
                return
            cols = [r['name'] for r in db.execute("PRAGMA table_info(ZUSER);").fetchall()]
            user_columns = {
                'ZBIRTHDATERAW': 'VARCHAR',
                'ZFIGOALRAW': 'FLOAT',
                'ZFIMONTHLYSIPRAW': 'FLOAT',
                'ZFIRETURNRATERAW': 'FLOAT',
                'ZFIINFLATIONRATERAW': 'FLOAT',
                'ZFISWRRAW': 'FLOAT',
                'ZGOOGLEID': 'VARCHAR',
                'ZEMAIL': 'VARCHAR',
                'ZAVATARURL': 'VARCHAR',
                'ZCDRIVETOKEN': 'TEXT',
                'ZISLOGGEDIN': 'INTEGER'
            }
            for col_name, col_type in user_columns.items():
                if col_name not in cols:
                    try:
                        db.execute(f"ALTER TABLE ZUSER ADD COLUMN {col_name} {col_type};")
                        db.commit()
                    except Exception:
                        pass
        except Exception:
            pass

    @staticmethod
    def get_user():
        UserRepository._ensure_fi_columns()
        db = get_db()
        try:
            tbl_check = db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ZUSER';").fetchone()
            if not tbl_check:
                return None
            row = db.execute("SELECT * FROM ZUSER LIMIT 1;").fetchone()
            return UserRepository._map_row(row) if row else None
        except Exception:
            return None

    @staticmethod
    def get_active_google_user():
        user = UserRepository.get_user()
        if user and user.get('is_logged_in') == 1 and (user.get('email') or user.get('google_id')):
            return user
        return None

    @staticmethod
    def save_google_login(google_id: str, email: str, name: str, avatar_url: str = None, token: str = None):
        UserRepository._ensure_fi_columns()
        user = UserRepository.get_user()
        db = get_db()
        if user:
            db.execute(
                "UPDATE ZUSER SET ZGOOGLEID = ?, ZEMAIL = ?, ZUSERNAME = ?, ZAVATARURL = ?, ZCDRIVETOKEN = COALESCE(?, ZCDRIVETOKEN), ZISLOGGEDIN = 1 WHERE Z_PK = ?;",
                (google_id, email, name, avatar_url, token, user['id'])
            )
            db.commit()
            return user['id']
        else:
            new_pk = get_next_pk("User")
            db.execute(
                "INSERT INTO ZUSER (Z_PK, Z_ENT, Z_OPT, ZUSERNAME, ZTAXSLABRATERAW, ZGOOGLEID, ZEMAIL, ZAVATARURL, ZCDRIVETOKEN, ZISLOGGEDIN) VALUES (?, 5, 1, ?, 0.30, ?, ?, ?, ?, 1);",
                (new_pk, name, google_id, email, avatar_url, token)
            )
            db.commit()
            return new_pk

    @staticmethod
    def clear_google_login():
        UserRepository._ensure_fi_columns()
        user = UserRepository.get_user()
        if user:
            db = get_db()
            db.execute("UPDATE ZUSER SET ZISLOGGEDIN = 0 WHERE Z_PK = ?;", (user['id'],))
            db.commit()

    @staticmethod
    def create_or_update(username: str, slab_rate: float = 0.30, birth_date: str = None) -> int:
        UserRepository._ensure_fi_columns()
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
    def update_google_user(google_id: str, email: str, name: str, avatar_url: str = None, token: str = None):
        return UserRepository.save_google_login(google_id, email, name, avatar_url, token)

    @staticmethod
    def update_gdrive_token(token: str):
        UserRepository._ensure_fi_columns()
        user = UserRepository.get_user()
        if user:
            db = get_db()
            db.execute("UPDATE ZUSER SET ZCDRIVETOKEN = ? WHERE Z_PK = ?;", (token, user['id']))
            db.commit()

    @staticmethod
    def update_birth_date(birth_date: str):
        UserRepository._ensure_fi_columns()
        user = UserRepository.get_user()
        if user:
            db = get_db()
            db.execute("UPDATE ZUSER SET ZBIRTHDATERAW = ? WHERE Z_PK = ?;", (birth_date, user['id']))
            db.commit()
        else:
            UserRepository.create_or_update(username="Portfolio User", birth_date=birth_date)

    @staticmethod
    def update_fi_details(target_goal: float, monthly_sip: float, return_rate: float, inflation_rate: float, swr: float, birth_date: str = None):
        UserRepository._ensure_fi_columns()
        user = UserRepository.get_user()
        db = get_db()
        if user:
            if birth_date:
                db.execute(
                    "UPDATE ZUSER SET ZFIGOALRAW = ?, ZFIMONTHLYSIPRAW = ?, ZFIRETURNRATERAW = ?, ZFIINFLATIONRATERAW = ?, ZFISWRRAW = ?, ZBIRTHDATERAW = ? WHERE Z_PK = ?;",
                    (target_goal, monthly_sip, return_rate, inflation_rate, swr, birth_date, user['id'])
                )
            else:
                db.execute(
                    "UPDATE ZUSER SET ZFIGOALRAW = ?, ZFIMONTHLYSIPRAW = ?, ZFIRETURNRATERAW = ?, ZFIINFLATIONRATERAW = ?, ZFISWRRAW = ? WHERE Z_PK = ?;",
                    (target_goal, monthly_sip, return_rate, inflation_rate, swr, user['id'])
                )
            db.commit()
        else:
            new_pk = get_next_pk("User")
            db.execute(
                "INSERT INTO ZUSER (Z_PK, Z_ENT, Z_OPT, ZUSERNAME, ZTAXSLABRATERAW, ZFIGOALRAW, ZFIMONTHLYSIPRAW, ZFIRETURNRATERAW, ZFIINFLATIONRATERAW, ZFISWRRAW, ZBIRTHDATERAW) VALUES (?, 5, 1, 'Portfolio User', 0.30, ?, ?, ?, ?, ?, ?);",
                (new_pk, target_goal, monthly_sip, return_rate, inflation_rate, swr, birth_date)
            )
            db.commit()

    @staticmethod
    def _map_row(r):
        if not r: return None
        d = dict(r)
        return {
            'id': d['Z_PK'],
            'username': d.get('ZUSERNAME', ''),
            'email': d.get('ZEMAIL') or '',
            'google_id': d.get('ZGOOGLEID') or '',
            'avatar_url': d.get('ZAVATARURL') or '',
            'gdrive_token': d.get('ZCDRIVETOKEN') or '',
            'is_logged_in': d.get('ZISLOGGEDIN', 0) or 0,
            'tax_slab_rate': d.get('ZTAXSLABRATERAW', 0.30) or 0.30,
            'birth_date': d.get('ZBIRTHDATERAW') or None,
            'target_goal': d.get('ZFIGOALRAW') if d.get('ZFIGOALRAW') is not None else 70000000.0,
            'monthly_sip': d.get('ZFIMONTHLYSIPRAW') if d.get('ZFIMONTHLYSIPRAW') is not None else 50000.0,
            'return_rate': d.get('ZFIRETURNRATERAW') if d.get('ZFIRETURNRATERAW') is not None else 12.0,
            'inflation_rate': d.get('ZFIINFLATIONRATERAW') if d.get('ZFIINFLATIONRATERAW') is not None else 6.0,
            'swr': d.get('ZFISWRRAW') if d.get('ZFISWRRAW') is not None else 4.0
        }

