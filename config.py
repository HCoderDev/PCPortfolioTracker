import os
import sys

import shutil

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_database_path():
    if os.environ.get("DATABASE_PATH"):
        return os.environ.get("DATABASE_PATH")

    db_filename = "PortfolioTrackerBackup-2026-07-26.db"
    dev_data_db = os.path.join(BASE_DIR, "Data", db_filename)

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        exe_data_db = os.path.join(exe_dir, "Data", db_filename)

        if os.path.exists(exe_data_db):
            return exe_data_db

        appdata = os.environ.get('APPDATA') or os.path.expanduser('~')
        user_data_dir = os.path.join(appdata, 'iPortfolioTracker', 'Data')
        os.makedirs(user_data_dir, exist_ok=True)
        user_db_path = os.path.join(user_data_dir, db_filename)

        if not os.path.exists(user_db_path):
            bundle_db = os.path.join(BASE_DIR, "Data", db_filename)
            if os.path.exists(bundle_db):
                try:
                    shutil.copy2(bundle_db, user_db_path)
                except Exception:
                    pass

        return user_db_path

    if os.path.exists(dev_data_db):
        return dev_data_db

    return dev_data_db

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "iportfolio-tracker-secret-key-2026")
    DATABASE_PATH = get_database_path()
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
