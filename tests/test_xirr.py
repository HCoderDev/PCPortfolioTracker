import unittest
from datetime import datetime, timezone
from app.services.xirr_service import XirrService, CashFlow

class TestXirrService(unittest.TestCase):
    def test_xirr_calculation(self):
        cfs = [
            CashFlow(amount=-10000.0, date=datetime(2023, 1, 1, tzinfo=timezone.utc)),
            CashFlow(amount=11000.0, date=datetime(2024, 1, 1, tzinfo=timezone.utc))
        ]

        rate = XirrService.calculate_xirr(cfs)
        self.assertIsNotNone(rate)
        # Should be approximately 10.0%
        self.assertAlmostEqual(rate, 10.0, delta=0.5)

if __name__ == '__main__':
    unittest.main()
