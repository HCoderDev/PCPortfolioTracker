import pytest
import os
import io
import sqlite3
from datetime import datetime, timezone
from app import create_app
from app.db import get_db, get_next_pk
from app.utils.date_utils import datetime_to_core_data_timestamp, core_data_timestamp_to_datetime
from app.repositories.asset_repository import AssetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.broker_repository import BrokerRepository

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_core_data_date_conversion():
    # Core Data epoch: 2001-01-01 00:00:00 UTC
    dt = datetime(2001, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    ts = datetime_to_core_data_timestamp(dt)
    assert ts == 0.0

    converted_dt = core_data_timestamp_to_datetime(0.0)
    assert converted_dt == dt

def test_repositories_read(app):
    with app.app_context():
        assets = AssetRepository.get_all()
        assert isinstance(assets, list)
        assert len(assets) > 0

        categories = CategoryRepository.get_all()
        assert isinstance(categories, list)
        assert len(categories) > 0

        currencies = CurrencyRepository.get_all()
        assert isinstance(currencies, list)
        assert len(currencies) > 0

        brokers = BrokerRepository.get_all()
        assert isinstance(brokers, list)
        assert len(brokers) > 0

def test_export_and_import_db_routes(client, tmp_path):
    # Test export download route
    response = client.get('/export/db/download')
    assert response.status_code == 200
    assert response.data.startswith(b'SQLite format 3\x00')

    # Test invalid file import
    invalid_data = (io.BytesIO(b'Not a sqlite database'), 'test.db')
    resp_invalid = client.post('/export/db/import', data={'db_file': invalid_data}, content_type='multipart/form-data', follow_redirects=True)
    assert b"Invalid file format" in resp_invalid.data

    # Backup original DB content before testing valid blind import
    from config import Config
    db_path = Config.DATABASE_PATH
    with open(db_path, 'rb') as f:
        original_db_bytes = f.read()

    # Test valid SQLite database import (blind replacement)
    temp_db_file = tmp_path / "valid_test.db"
    conn = sqlite3.connect(str(temp_db_file))
    conn.execute("CREATE TABLE test_tbl (id INT);")
    conn.commit()
    conn.close()

    with open(temp_db_file, 'rb') as f:
        valid_bytes = f.read()

    valid_upload = (io.BytesIO(valid_bytes), 'valid_test.db')
    resp_valid = client.post('/export/db/import', data={'db_file': valid_upload}, content_type='multipart/form-data', follow_redirects=True)
    assert b"Database content blindly replaced and imported successfully" in resp_valid.data

    # Restore original DB content for remaining test session
    with open(db_path, 'wb') as f:
        f.write(original_db_bytes)


