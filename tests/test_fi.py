import pytest
from datetime import datetime, timezone
from app import create_app
from app.services.fi_service import FiService
from app.repositories.user_repository import UserRepository

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

def test_fi_projection():
    res = FiService.project_fi(
        current_net_worth=1000000.0,
        target_goal=10000000.0,
        birth_date=datetime(1995, 1, 1, tzinfo=timezone.utc),
        monthly_sip=50000.0,
        return_rate=12.0,
        inflation_rate=6.0,
        safe_withdrawal_rate=4.0
    )

    assert res.months_needed > 0
    assert res.annual_passive_income_at_fi > 0
    assert len(res.milestones) == 4

def test_fi_details_persistence(app, client):
    with app.app_context():
        UserRepository.update_fi_details(
            target_goal=85000000.0,
            monthly_sip=75000.0,
            return_rate=13.5,
            inflation_rate=5.5,
            swr=3.5,
            birth_date="1992-05-15"
        )

        user = UserRepository.get_user()
        assert user is not None
        assert user['target_goal'] == 85000000.0
        assert user['monthly_sip'] == 75000.0
        assert user['return_rate'] == 13.5
        assert user['inflation_rate'] == 5.5
        assert user['swr'] == 3.5
        assert user['birth_date'] == "1992-05-15"

    response = client.post('/fi-tracker', data={
        'target_goal': '90000000',
        'monthly_sip': '80000',
        'return_rate': '14',
        'inflation_rate': '6',
        'swr': '4',
        'birth_date': '1990-10-10'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'value="1990-10-10"' in response.data
    assert b'DOB: 10-10-1990' in response.data

    with app.app_context():
        user = UserRepository.get_user()
        assert user['target_goal'] == 90000000.0
        assert user['monthly_sip'] == 80000.0
        assert user['return_rate'] == 14.0
        assert user['inflation_rate'] == 6.0
        assert user['swr'] == 4.0
        assert user['birth_date'] == '1990-10-10'

