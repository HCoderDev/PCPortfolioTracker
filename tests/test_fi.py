import unittest
from datetime import datetime, timezone
from app.services.fi_service import FiService

class TestFiService(unittest.TestCase):
    def test_fi_projection(self):
        res = FiService.project_fi(
            current_net_worth=1000000.0,
            target_goal=10000000.0,
            birth_date=datetime(1995, 1, 1, tzinfo=timezone.utc),
            monthly_sip=50000.0,
            return_rate=12.0,
            inflation_rate=6.0,
            safe_withdrawal_rate=4.0
        )

        self.assertGreater(res.months_needed, 0)
        self.assertGreater(res.annual_passive_income_at_fi, 0)
        self.assertEqual(len(res.milestones), 4)

if __name__ == '__main__':
    unittest.main()
