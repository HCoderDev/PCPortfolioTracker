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

def test_valuation_tab_rendering(client, app):
    with app.app_context():
        all_assets = AssetRepository.get_all()
        
        # Find asset in Individual Equity category (e.g. Indian Stocks / US Stocks)
        equity_asset = next((a for a in all_assets if a.get('holding_type') == 'investment' and CategoryRepository.get_by_id(a['category_id']).get('is_individual_equity')), None)
        
        # Find asset in non-Individual Equity category (e.g. Mutual Funds)
        non_equity_asset = next((a for a in all_assets if a.get('holding_type') == 'investment' and not CategoryRepository.get_by_id(a['category_id']).get('is_individual_equity')), None)

        if equity_asset:
            res_eq = client.get(f"/assets/{equity_asset['id']}")
            assert res_eq.status_code == 200
            assert b'id="tab-valuation"' in res_eq.data
            assert b'id="content-valuation"' in res_eq.data

        if non_equity_asset:
            res_non_eq = client.get(f"/assets/{non_equity_asset['id']}")
            assert res_non_eq.status_code == 200
            assert b'id="tab-valuation"' not in res_non_eq.data
            assert b'id="content-valuation"' not in res_non_eq.data
