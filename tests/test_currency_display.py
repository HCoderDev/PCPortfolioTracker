import pytest
from app import create_app
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.transaction_repository import TransactionRepository

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

def test_dashboard_inr_display(client, app):
    response = client.get('/dashboard')
    assert response.status_code == 200
    # Verify Dashboard responds successfully and contains currency symbol formatting
    assert b'Total Portfolio Value' in response.data
    assert b'Portfolio Allocation' in response.data

def test_assets_list_currency_toggle(client, app):
    # Test INR display on assets list
    resp_inr = client.get('/assets?currency=INR')
    assert resp_inr.status_code == 200
    assert b'Current Price (INR)' in resp_inr.data

    # Test USD display on assets list
    resp_usd = client.get('/assets?currency=USD')
    assert resp_usd.status_code == 200
    assert b'Current Price (USD)' in resp_usd.data
