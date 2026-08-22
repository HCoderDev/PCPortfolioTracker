import os
import sys

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_database_path():
    if os.environ.get("DATABASE_PATH"):
        return os.environ.get("DATABASE_PATH")

    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates = [
            os.path.join(exe_dir, "Data", "PortfolioTrackerBackup-2026-07-26.db"),
            os.path.join(exe_dir, "..", "..", "Data", "PortfolioTrackerBackup-2026-07-26.db"),
            os.path.join(os.getcwd(), "Data", "PortfolioTrackerBackup-2026-07-26.db"),
            os.path.join(BASE_DIR, "Data", "PortfolioTrackerBackup-2026-07-26.db"),
        ]
        for path in candidates:
            norm_path = os.path.abspath(path)
            if os.path.exists(norm_path):
                return norm_path

    return os.path.join(BASE_DIR, "Data", "PortfolioTrackerBackup-2026-07-26.db")

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "iportfolio-tracker-secret-key-2026")
    DATABASE_PATH = get_database_path()
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ("true", "1", "t")
