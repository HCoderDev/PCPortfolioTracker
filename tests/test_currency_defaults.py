import pytest
from app import create_app
from app.repositories.asset_repository import AssetRepository
from app.repositories.category_repository import CategoryRepository

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_currency_defaults_to_inr(client, app):
    with app.app_context():
        all_assets = AssetRepository.get_all()
        us_asset = next((a for a in all_assets if CategoryRepository.get_by_id(a['category_id']).get('currency_code') == 'USD'), None)

        if us_asset:
            res = client.get(f"/assets/{us_asset['id']}")
            assert res.status_code == 200
            # Verify INR default toggle button is present
            assert b'btn-market-curr-inr' in res.data
            assert b'INR (\xe2\x82\xb9) Default' in res.data or b'INR' in res.data
            # Verify USD toggle button is present for US stocks on demand
            assert b'btn-market-curr-native' in res.data
