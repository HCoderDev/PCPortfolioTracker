import pytest
from datetime import datetime
from app import create_app
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.services.transaction_type_registry import TransactionTypeRegistry
from app.routes.passive_income import is_passive_income_tx

@pytest.fixture
def app():
    app = create_app()
    app.config.update({"TESTING": True})
    yield app

def test_transaction_type_registry_holding_types():
    holding_types = ['investment', 'bankBalance', 'fixedDeposit', 'postOffice', 'epf', 'insuranceAnnuity']
    for h in holding_types:
        config = TransactionTypeRegistry.get_config_for_holding_type(h)
        assert config is not None
        assert 'allowed_transactions' in config
        assert len(config['allowed_transactions']) > 0

def test_category_allowed_passive_types(app):
    with app.app_context():
        categories = CategoryRepository.get_all()
        if categories:
            cat = categories[0]
            allowed = CategoryRepository.allowed_passive_transaction_types(cat['id'], cat['name'])
            assert isinstance(allowed, list)
            assert len(allowed) > 0

def test_passive_income_rule_filtering():
    category = {
        'id': 1,
        'name': 'Test Category',
        'passive_transaction_types': {'DIVIDEND', 'INTEREST', 'BONUS'}
    }
    
    div_tx = {'type': 'DIVIDEND', 'raw_type': 'DIVIDEND'}
    int_tx = {'type': 'INTEREST', 'raw_type': 'INTEREST'}
    buy_tx = {'type': 'BUY', 'raw_type': 'BUY'}
    
    assert is_passive_income_tx(div_tx, category) is True
    assert is_passive_income_tx(int_tx, category) is True
    assert is_passive_income_tx(buy_tx, category) is False

def test_asset_holding_type_edit(app):
    with app.app_context():
        assets = AssetRepository.get_all()
        if assets:
            target = assets[0]
            orig_holding_type = target['holding_type']
            data = dict(target)
            data['holding_type'] = 'insuranceAnnuity'
            data['policy_number'] = 'POL-998877'
            data['premium_amount'] = 25000.0
            data['premium_term_years'] = 10
            data['institution_name'] = 'LIC India'
            data['is_completed'] = True
            
            AssetRepository.update(target['id'], data)
            updated = AssetRepository.get_by_id(target['id'])
            assert updated['holding_type'] == 'insuranceAnnuity'
            assert updated['policy_number'] == 'POL-998877'
            assert updated['premium_amount'] == 25000.0
            assert updated['premium_term_years'] == 10
            assert updated['institution_name'] == 'LIC India'
            assert updated['is_completed'] is True

            # Restore original holding type
            data['holding_type'] = orig_holding_type
            AssetRepository.update(target['id'], data)

def test_category_last_updated_on_balance_update(app):
    with app.app_context():
        client = app.test_client()
        assets = AssetRepository.get_all()
        if assets:
            target = assets[0]
            cat_id = target['category_id']
            res = client.post(f'/assets/update-balance/{target["id"]}', data={'current_balance': '75000.0'})
            assert res.status_code in [200, 302]
            if cat_id:
                cat = CategoryRepository.get_by_id(cat_id)
                assert cat['last_updated_date'] is not None
