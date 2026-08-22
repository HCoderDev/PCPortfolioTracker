from datetime import datetime, timezone
import math

class TaxClassification:
    STCG = "STCG"
    LTCG = "LTCG"
    SLAB = "Slab Rate (Debt)"

class HoldingLot:
    def __init__(self, original_units: float, remaining_units: float, buy_price: float, date: datetime):
        self.original_units = original_units
        self.remaining_units = remaining_units
        self.buy_price = buy_price
        self.date = date

class HoldingLotINR:
    def __init__(self, original_units: float, remaining_units: float, buy_price: float, buy_price_inr: float, date: datetime):
        self.original_units = original_units
        self.remaining_units = remaining_units
        self.buy_price = buy_price
        self.buy_price_inr = buy_price_inr
        self.date = date

class FifoResult:
    def __init__(self, realized_profit_loss: float, lifetime_invested: float, lifetime_retrieved: float, holdings: list):
        self.realized_profit_loss = realized_profit_loss
        self.lifetime_invested = lifetime_invested
        self.lifetime_retrieved = lifetime_retrieved
        self.holdings = holdings

class FifoResultINR:
    def __init__(self, realized_profit_loss: float, lifetime_invested: float, lifetime_retrieved: float, holdings: list):
        self.realized_profit_loss = realized_profit_loss
        self.lifetime_invested = lifetime_invested
        self.lifetime_retrieved = lifetime_retrieved
        self.holdings = holdings

class FifoHoldingLot:
    def __init__(self, purchase_date: datetime, original_units: float, remaining_units: float, buy_price: float, buy_price_inr: float, tax_category: str, tax_rate: float, holding_age_days: int, current_price: float, current_price_inr: float):
        self.purchase_date = purchase_date
        self.original_units = original_units
        self.remaining_units = remaining_units
        self.buy_price = buy_price
        self.buy_price_inr = buy_price_inr
        self.tax_category = tax_category
        self.tax_rate = tax_rate
        self.holding_age_days = holding_age_days
        self.current_price = current_price
        self.current_price_inr = current_price_inr

    @property
    def unrealized_gain(self) -> float:
        return (self.current_price - self.buy_price) * self.remaining_units

    @property
    def unrealized_gain_inr(self) -> float:
        return (self.current_price_inr - self.buy_price_inr) * self.remaining_units

class FifoRealizedTrade:
    def __init__(self, sell_date: datetime, buy_date: datetime, units: float, buy_price: float, buy_price_inr: float, sell_price: float, sell_price_inr: float, tax_category: str, tax_rate: float):
        self.sell_date = sell_date
        self.buy_date = buy_date
        self.units = units
        self.buy_price = buy_price
        self.buy_price_inr = buy_price_inr
        self.sell_price = sell_price
        self.sell_price_inr = sell_price_inr
        self.tax_category = tax_category
        self.tax_rate = tax_rate

    @property
    def realized_gain(self) -> float:
        return (self.sell_price - self.buy_price) * self.units

    @property
    def realized_gain_inr(self) -> float:
        return (self.sell_price_inr - self.buy_price_inr) * self.units

class FifoTaxResult:
    def __init__(self, active_lots: list, realized_trades_current_fy: list):
        self.active_lots = active_lots
        self.realized_trades_current_fy = realized_trades_current_fy

    @property
    def total_unrealized_stcg_gains(self) -> float:
        return sum(max(0, lot.unrealized_gain_inr) for lot in self.active_lots if lot.tax_category == TaxClassification.STCG)

    @property
    def total_unrealized_ltcg_gains(self) -> float:
        return sum(max(0, lot.unrealized_gain_inr) for lot in self.active_lots if lot.tax_category == TaxClassification.LTCG)

    @property
    def total_unrealized_slab_gains(self) -> float:
        return sum(max(0, lot.unrealized_gain_inr) for lot in self.active_lots if lot.tax_category == TaxClassification.SLAB)

    @property
    def total_unrealized_tax(self) -> float:
        stcg_tax = sum(max(0, lot.unrealized_gain_inr * lot.tax_rate) for lot in self.active_lots if lot.tax_category == TaxClassification.STCG)
        ltcg_tax = sum(max(0, lot.unrealized_gain_inr * lot.tax_rate) for lot in self.active_lots if lot.tax_category == TaxClassification.LTCG)
        slab_tax = sum(max(0, lot.unrealized_gain_inr * lot.tax_rate) for lot in self.active_lots if lot.tax_category == TaxClassification.SLAB)
        return stcg_tax + ltcg_tax + slab_tax

    @property
    def total_realized_stcg_gains(self) -> float:
        return sum(t.realized_gain_inr for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.STCG)

    @property
    def total_realized_ltcg_gains(self) -> float:
        return sum(t.realized_gain_inr for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.LTCG)

    @property
    def total_realized_slab_gains(self) -> float:
        return sum(t.realized_gain_inr for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.SLAB)

    @property
    def total_realized_tax(self) -> float:
        stcg_tax = sum(max(0, t.realized_gain_inr * t.tax_rate) for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.STCG)
        ltcg_tax = sum(max(0, t.realized_gain_inr * t.tax_rate) for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.LTCG)
        slab_tax = sum(max(0, t.realized_gain_inr * t.tax_rate) for t in self.realized_trades_current_fy if t.tax_category == TaxClassification.SLAB)
        return stcg_tax + ltcg_tax + slab_tax


class FifoService:
    @staticmethod
    def is_in_current_financial_year(dt: datetime, as_of_date: datetime = None) -> bool:
        """Indian Financial Year starts April 1st."""
        if dt is None: return False
        ref = as_of_date or datetime.now(timezone.utc)
        curr_year = ref.year
        curr_month = ref.month
        fy_start_year = curr_year if curr_month >= 4 else curr_year - 1
        fy_start = datetime(fy_start_year, 4, 1, tzinfo=timezone.utc)
        return dt >= fy_start and dt <= ref

    @staticmethod
    def determine_tax_class(country: str, asset_type: str, buy_date: datetime, valuation_date: datetime, slab_rate: float = 0.30, ltcg_threshold_months: int = None) -> tuple:
        if asset_type == "debt":
            return (TaxClassification.SLAB, slab_rate)

        threshold_months = ltcg_threshold_months if ltcg_threshold_months else (24 if country == "United States" or country == "us" else (12 if asset_type == "equity" else 36))
        days = (valuation_date - buy_date).days
        threshold_days = int(threshold_months * 30.4375)

        if days > threshold_days:
            return (TaxClassification.LTCG, 0.125)
        else:
            return (TaxClassification.STCG, 0.20)

    @staticmethod
    def calculate(transactions: list) -> FifoResult:
        sorted_txs = sorted(transactions, key=lambda x: (x['date'], x.get('created_at', x['date'])))
        buy_lots = []
        realized_pl = 0.0

        lifetime_invested = sum(tx['price_per_unit'] * tx['units'] for tx in transactions if tx['type'] == 'BUY')
        lifetime_retrieved = sum(tx['price_per_unit'] * (tx['units'] if tx['type'] == 'SELL' else 1.0) for tx in transactions if tx['type'] in ['SELL', 'DIVIDEND'])

        for tx in sorted_txs:
            tx_type = tx['type']
            if tx_type == 'BUY':
                buy_lots.append({
                    'original_units': tx['units'],
                    'remaining_units': tx['units'],
                    'buy_price': tx['price_per_unit'],
                    'date': tx['date']
                })
            elif tx_type == 'SELL':
                units_to_sell = tx['units']
                sell_price = tx['price_per_unit']
                for lot in buy_lots:
                    if units_to_sell <= 0: break
                    if lot['remaining_units'] > 0:
                        units_taken = min(units_to_sell, lot['remaining_units'])
                        invested = lot['buy_price'] * units_taken
                        retrieved = sell_price * units_taken
                        realized_pl += (retrieved - invested)
                        lot['remaining_units'] -= units_taken
                        units_to_sell -= units_taken
            elif tx_type == 'DIVIDEND':
                amount = tx['price_per_unit'] if tx.get('units', 0.0) == 0.0 else tx['price_per_unit'] * tx['units']
                realized_pl += amount

        holdings = [HoldingLot(l['original_units'], l['remaining_units'], l['buy_price'], l['date']) for l in buy_lots if l['remaining_units'] > 1e-6]
        return FifoResult(realized_pl, lifetime_invested, lifetime_retrieved, holdings)

    @staticmethod
    def calculate_in_inr(transactions: list, category_exchange_rate: float) -> FifoResultINR:
        sorted_txs = sorted(transactions, key=lambda x: (x['date'], x.get('created_at', x['date'])))
        buy_lots = []
        realized_pl = 0.0

        lifetime_invested = 0.0
        lifetime_retrieved = 0.0

        for tx in transactions:
            rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else category_exchange_rate
            amt = tx['price_per_unit'] * (tx['units'] if tx['type'] in ['BUY', 'SELL'] else 1.0)
            if tx['type'] == 'BUY':
                lifetime_invested += (amt * rate)
            elif tx['type'] in ['SELL', 'DIVIDEND']:
                lifetime_retrieved += (amt * rate)

        for tx in sorted_txs:
            tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else category_exchange_rate
            tx_type = tx['type']

            if tx_type == 'BUY':
                buy_lots.append({
                    'original_units': tx['units'],
                    'remaining_units': tx['units'],
                    'buy_price': tx['price_per_unit'],
                    'buy_rate': tx_rate,
                    'date': tx['date']
                })
            elif tx_type == 'SELL':
                units_to_sell = tx['units']
                sell_price = tx['price_per_unit']
                for lot in buy_lots:
                    if units_to_sell <= 0: break
                    if lot['remaining_units'] > 0:
                        units_taken = min(units_to_sell, lot['remaining_units'])
                        invested = lot['buy_price'] * units_taken * lot['buy_rate']
                        retrieved = sell_price * units_taken * tx_rate
                        realized_pl += (retrieved - invested)
                        lot['remaining_units'] -= units_taken
                        units_to_sell -= units_taken
            elif tx_type == 'DIVIDEND':
                amount = tx['price_per_unit'] if tx.get('units', 0.0) == 0.0 else tx['price_per_unit'] * tx['units']
                realized_pl += (amount * tx_rate)

        holdings = [HoldingLotINR(l['original_units'], l['remaining_units'], l['buy_price'], l['buy_price'] * l['buy_rate'], l['date']) for l in buy_lots if l['remaining_units'] > 1e-6]
        return FifoResultINR(realized_pl, lifetime_invested, lifetime_retrieved, holdings)

    @staticmethod
    def calculate_tax(asset: dict, transactions: list, category_exchange_rate: float, slab_rate: float = 0.30) -> FifoTaxResult:
        sorted_txs = sorted(transactions, key=lambda x: (x['date'], x.get('created_at', x['date'])))
        custom_months = asset.get('ltcg_threshold_months')
        buy_lots = []
        realized_trades = []

        for tx in sorted_txs:
            tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else category_exchange_rate
            tx_type = tx['type']

            if tx_type == 'BUY':
                buy_lots.append({
                    'original_units': tx['units'],
                    'remaining_units': tx['units'],
                    'buy_price': tx['price_per_unit'],
                    'buy_rate': tx_rate,
                    'date': tx['date']
                })
            elif tx_type == 'SELL':
                units_to_sell = tx['units']
                sell_price = tx['price_per_unit']
                for lot in buy_lots:
                    if units_to_sell <= 0: break
                    if lot['remaining_units'] > 0:
                        units_taken = min(units_to_sell, lot['remaining_units'])
                        tax_cat, tax_r = FifoService.determine_tax_class(
                            country=asset.get('tax_country', 'India'),
                            asset_type=asset.get('tax_asset_type', 'equity'),
                            buy_date=lot['date'],
                            valuation_date=tx['date'],
                            slab_rate=slab_rate,
                            ltcg_threshold_months=custom_months
                        )
                        trade = FifoRealizedTrade(
                            sell_date=tx['date'],
                            buy_date=lot['date'],
                            units=units_taken,
                            buy_price=lot['buy_price'],
                            buy_price_inr=lot['buy_price'] * lot['buy_rate'],
                            sell_price=sell_price,
                            sell_price_inr=sell_price * tx_rate,
                            tax_category=tax_cat,
                            tax_rate=tax_r
                        )
                        if FifoService.is_in_current_financial_year(tx['date']):
                            realized_trades.append(trade)

                        lot['remaining_units'] -= units_taken
                        units_to_sell -= units_taken
            elif tx_type == 'DIVIDEND':
                if FifoService.is_in_current_financial_year(tx['date']):
                    div_income = tx['price_per_unit'] if tx.get('units', 0.0) == 0.0 else tx['price_per_unit'] * tx['units']
                    realized_trades.append(FifoRealizedTrade(
                        sell_date=tx['date'], buy_date=tx['date'], units=0.0,
                        buy_price=0.0, buy_price_inr=0.0, sell_price=div_income,
                        sell_price_inr=div_income * tx_rate, tax_category=TaxClassification.SLAB, tax_rate=slab_rate
                    ))

        now_dt = datetime.now(timezone.utc)
        active_lots = []
        if asset.get('holding_type') != 'investment': # Non-unitized asset
            active_lots = []
        else:
            for lot in buy_lots:
                if lot['remaining_units'] > 1e-6:
                    tax_cat, tax_r = FifoService.determine_tax_class(
                        country=asset.get('tax_country', 'India'),
                        asset_type=asset.get('tax_asset_type', 'equity'),
                        buy_date=lot['date'],
                        valuation_date=now_dt,
                        slab_rate=slab_rate,
                        ltcg_threshold_months=custom_months
                    )
                    age_days = (now_dt - lot['date']).days
                    active_lots.append(FifoHoldingLot(
                        purchase_date=lot['date'],
                        original_units=lot['original_units'],
                        remaining_units=lot['remaining_units'],
                        buy_price=lot['buy_price'],
                        buy_price_inr=lot['buy_price'] * lot['buy_rate'],
                        tax_category=tax_cat,
                        tax_rate=tax_r,
                        holding_age_days=age_days,
                        current_price=asset.get('current_price', 0.0),
                        current_price_inr=asset.get('current_price', 0.0) * category_exchange_rate
                    ))

        return FifoTaxResult(active_lots, realized_trades)
