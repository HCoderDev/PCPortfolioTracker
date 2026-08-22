import pytest
from app import create_app
from app.repositories.asset_repository import AssetRepository

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_update_bank_balance_endpoint(client, app):
    with app.app_context():
        # Find a bank account or contract asset
        all_assets = AssetRepository.get_all()
        bank_asset = next((a for a in all_assets if a.get('holding_type') == 'bankBalance'), all_assets[0])
        asset_id = bank_asset['id']
        orig_price = bank_asset['current_price']

        # Post update balance
        new_balance = 250000.50
        res = client.post(f'/assets/update-balance/{asset_id}', data={'current_balance': str(new_balance)}, follow_redirects=True)
        assert res.status_code == 200

        # Check DB updated
        updated_asset = AssetRepository.get_by_id(asset_id)
        assert abs(updated_asset['current_price'] - new_balance) < 1e-4

        # Restore original price
        AssetRepository.update_price(asset_id, orig_price)
