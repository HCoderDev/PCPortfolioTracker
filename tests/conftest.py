import os
import shutil
import tempfile
import pytest
from app import create_app
from config import Config

@pytest.fixture(scope="session", autouse=True)
def temp_db():
    orig_db = Config.DATABASE_PATH
    temp_dir = tempfile.mkdtemp()
    temp_db_path = os.path.join(temp_dir, "test_temp_db.sqlite")

    if os.path.exists(orig_db):
        shutil.copy(orig_db, temp_db_path)
    else:
        with open(temp_db_path, 'w') as f:
            f.write('')

    os.environ["DATABASE_PATH"] = temp_db_path
    Config.DATABASE_PATH = temp_db_path

    yield temp_db_path

    if os.path.exists(temp_db_path):
        try:
            os.remove(temp_db_path)
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
