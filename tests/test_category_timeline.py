from datetime import datetime, timezone
import pytest
from app import create_app
from app.db import get_db
from app.repositories.category_repository import CategoryRepository
from app.routes.categories import calculate_category_growth_timeline

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

def test_update_last_updated_date_repo(app):
    with app.app_context():
        # Create category
        cat_id = CategoryRepository.create({
            'name': 'Test Timeline Cat',
            'currency_code': 'INR'
        })
        cat = CategoryRepository.get_by_id(cat_id)
        assert cat is not None
        
        # Update last updated date
        now = datetime.now()
        CategoryRepository.update_last_updated_date(cat_id, now)
        
        cat_updated = CategoryRepository.get_by_id(cat_id)
        assert cat_updated['last_updated_date'] is not None
        assert cat_updated['last_updated_date'].year == now.year
        
        # Clear last updated date
        CategoryRepository.update_last_updated_date(cat_id, None)
        cat_cleared = CategoryRepository.get_by_id(cat_id)
        assert cat_cleared['last_updated_date'] is None

def test_update_last_updated_route(client, app):
    with app.app_context():
        cat_id = CategoryRepository.create({
            'name': 'Test Route Cat',
            'currency_code': 'INR'
        })

    # Action = today
    res = client.post(f'/categories/update-last-updated/{cat_id}', data={'action': 'today'}, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data['status'] == 'success'
    assert json_data['last_updated_date'] is not None

    # Action = clear
    res_clear = client.post(f'/categories/update-last-updated/{cat_id}', data={'action': 'clear'}, headers={'X-Requested-With': 'XMLHttpRequest'})
    assert res_clear.status_code == 200
    json_data_clear = res_clear.get_json()
    assert json_data_clear['status'] == 'success'
    assert json_data_clear['last_updated_date'] is None

def test_calculate_category_growth_timeline_empty():
    timeline = calculate_category_growth_timeline([])
    assert timeline == []
