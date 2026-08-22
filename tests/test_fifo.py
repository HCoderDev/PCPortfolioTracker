import unittest
from datetime import datetime, timezone
from app.services.fifo_service import FifoService, TaxClassification

class TestFifoService(unittest.TestCase):
    def test_fifo_lot_matching(self):
        txs = [
            {'type': 'BUY', 'units': 100.0, 'price_per_unit': 10.0, 'date': datetime(2022, 1, 1, tzinfo=timezone.utc)},
            {'type': 'BUY', 'units': 50.0, 'price_per_unit': 20.0, 'date': datetime(2022, 6, 1, tzinfo=timezone.utc)},
            {'type': 'SELL', 'units': 120.0, 'price_per_unit': 25.0, 'date': datetime(2023, 1, 1, tzinfo=timezone.utc)}
        ]

        res = FifoService.calculate(txs)
        # Sell 120 units: 100 units from Lot 1 @ $10 (Profit: 100 * (25-10) = 1500)
        #                 20 units from Lot 2 @ $20 (Profit: 20 * (25-20) = 100)
        # Total Realized P&L = 1600
        self.assertEqual(res.realized_profit_loss, 1600.0)

        # Remaining holdings: 30 units from Lot 2 @ $20
        self.assertEqual(len(res.holdings), 1)
        self.assertEqual(res.holdings[0].remaining_units, 30.0)
        self.assertEqual(res.holdings[0].buy_price, 20.0)

    def test_tax_classification(self):
        buy_date_ltcg = datetime(2021, 1, 1, tzinfo=timezone.utc)
        buy_date_stcg = datetime(2026, 1, 1, tzinfo=timezone.utc)
        val_date = datetime(2026, 6, 1, tzinfo=timezone.utc)

        ltcg_cat, ltcg_rate = FifoService.determine_tax_class("India", "equity", buy_date_ltcg, val_date)
        self.assertEqual(ltcg_cat, TaxClassification.LTCG)
        self.assertEqual(ltcg_rate, 0.125)

        stcg_cat, stcg_rate = FifoService.determine_tax_class("India", "equity", buy_date_stcg, val_date)
        self.assertEqual(stcg_cat, TaxClassification.STCG)
        self.assertEqual(stcg_rate, 0.20)

        debt_cat, debt_rate = FifoService.determine_tax_class("India", "debt", buy_date_ltcg, val_date, slab_rate=0.30)
        self.assertEqual(debt_cat, TaxClassification.SLAB)
        self.assertEqual(debt_rate, 0.30)

if __name__ == '__main__':
    unittest.main()
