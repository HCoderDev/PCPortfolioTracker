from datetime import datetime, timezone, timedelta
from app.services.transaction_registry import TransactionTypeRegistry, CashDirection
from app.services.fifo_service import FifoService
from app.services.xirr_service import XirrService, CashFlow

class InvestmentRecencyStatus:
    ACTIVE = "Active (<= 30d)"
    MODERATE = "Moderate (30-90d)"
    DORMANT = "Dormant (> 90d)"
    NEVER = "Never Invested"

class PortfolioService:
    @staticmethod
    def current_inr_exchange_rate(category: dict, currencies: list) -> float:
        if not category:
            return 1.0
        code = category.get('currency_code', 'INR')
        if code == "INR":
            return 1.0
        if category.get('last_inr_exchange_rate'):
            return float(category['last_inr_exchange_rate'])

        inr_curr = next((c for c in currencies if c['code'] == "INR"), None)
        cat_curr = next((c for c in currencies if c['code'] == code), None)

        if cat_curr and inr_curr and inr_curr['exchange_rate'] != 0:
            return float(cat_curr['exchange_rate']) / float(inr_curr['exchange_rate'])
        elif code == "USD":
            return 83.0
        return 1.0

    @staticmethod
    def total_units(transactions: list, holding_type: str = "investment") -> float:
        if holding_type != "investment":
            return 1.0

        total = 0.0
        for tx in transactions:
            tx_type = tx.get('type', 'BUY')
            raw_type = tx.get('raw_type', tx_type)
            cfg = TransactionTypeRegistry.config(raw_type, holding_type)

            if tx_type == 'DIVIDEND' or 'DIVIDEND' in raw_type.upper() or not cfg.is_unit_based:
                continue

            if tx_type == 'BUY':
                total += tx.get('units', 0.0)
            elif tx_type == 'SELL':
                total -= tx.get('units', 0.0)

        return 0.0 if abs(total) < 1e-6 else total

    @staticmethod
    def is_sold_off(asset: dict, transactions: list) -> bool:
        if asset.get('is_completed'):
            return True
        holding_type = asset.get('holding_type', 'investment')
        if holding_type != 'investment':
            return any(TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type).closes_asset for tx in transactions)

        rem_units = PortfolioService.total_units(transactions, holding_type)
        has_buy = any(tx['type'] == 'BUY' for tx in transactions)
        return abs(rem_units) <= 1e-6 and has_buy

    @staticmethod
    def invested_value(asset: dict, transactions: list) -> float:
        if PortfolioService.is_sold_off(asset, transactions):
            return 0.0

        holding_type = asset.get('holding_type', 'investment')
        if holding_type != 'investment':
            tx_invested = 0.0
            for tx in transactions:
                cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
                if cfg.affects_invested_amount:
                    amt = tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0)
                    if cfg.cash_direction == CashDirection.OUTFLOW:
                        tx_invested += amt
                    elif cfg.cash_direction == CashDirection.INFLOW:
                        tx_invested -= amt

            if tx_invested > 0:
                return tx_invested
            if asset.get('principal_amount', 0.0) > 0:
                return asset['principal_amount']
            if asset.get('premium_amount', 0.0) > 0:
                return asset['premium_amount']
            return max(0.0, asset.get('current_price', 0.0))

        fifo_res = FifoService.calculate(transactions)
        return sum(lot.remaining_units * lot.buy_price for lot in fifo_res.holdings)

    @staticmethod
    def current_value(asset: dict, transactions: list) -> float:
        if PortfolioService.is_sold_off(asset, transactions):
            return 0.0

        holding_type = asset.get('holding_type', 'investment')
        if holding_type != 'investment':
            if asset.get('current_price', 0.0) > 0:
                return asset['current_price']

            tx_bal = 0.0
            for tx in transactions:
                cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
                if cfg.affects_asset_value:
                    amt = tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0)
                    if cfg.cash_direction in [CashDirection.OUTFLOW, CashDirection.INTERNAL_ACCRUAL]:
                        tx_bal += amt
                    elif cfg.cash_direction == CashDirection.INFLOW:
                        tx_bal -= amt

            if tx_bal > 0:
                return tx_bal
            if asset.get('principal_amount', 0.0) > 0:
                return asset['principal_amount']
            if asset.get('premium_amount', 0.0) > 0:
                return asset['premium_amount']
            return 0.0

        units = PortfolioService.total_units(transactions, holding_type)
        return units * asset.get('current_price', 0.0)

    @staticmethod
    def invested_value_inr(asset: dict, transactions: list, rate: float) -> float:
        if asset.get('holding_type') != 'investment':
            return PortfolioService.invested_value(asset, transactions) * rate
        fifo_inr = FifoService.calculate_in_inr(transactions, rate)
        return sum(lot.remaining_units * lot.buy_price_inr for lot in fifo_inr.holdings)

    @staticmethod
    def current_value_inr(asset: dict, transactions: list, rate: float) -> float:
        return PortfolioService.current_value(asset, transactions) * rate

    @staticmethod
    def cash_flows(asset: dict, transactions: list, mode: str = "lifetime", valuation_date: datetime = None) -> list:
        val_date = valuation_date or datetime.now(timezone.utc)
        holding_type = asset.get('holding_type', 'investment')
        cfs = []

        sorted_txs = sorted(transactions, key=lambda x: (x['date'], x.get('created_at', x['date'])))

        if mode == "active" and holding_type == "investment" and any(tx['type'] == 'SELL' for tx in transactions):
            fifo_res = FifoService.calculate(transactions)
            holdings = fifo_res.holdings
            if not holdings: return []

            for lot in holdings:
                cfs.append(CashFlow(amount=-(lot.remaining_units * lot.buy_price), date=lot.date))

            oldest_active_date = min(lot.date for lot in holdings)
            for tx in transactions:
                if tx['type'] == 'DIVIDEND' and tx['date'] >= oldest_active_date:
                    amt = tx['price_per_unit'] * (tx['units'] if tx['units'] > 0 else 1.0)
                    cfs.append(CashFlow(amount=amt, date=tx['date']))
        else:
            for tx in sorted_txs:
                cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
                amt = tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0)
                raw_u = tx.get('raw_type', tx['type']).upper()

                if cfg.cash_direction == CashDirection.OUTFLOW:
                    cfs.append(CashFlow(amount=-amt, date=tx['date']))
                elif cfg.cash_direction in [CashDirection.INFLOW, CashDirection.INTERNAL_ACCRUAL] or tx['type'] == 'DIVIDEND' or 'DIVIDEND' in raw_u:
                    cfs.append(CashFlow(amount=amt, date=tx['date']))

        curr_val = PortfolioService.current_value(asset, transactions)
        if curr_val > 0 and not PortfolioService.is_sold_off(asset, transactions):
            cfs.append(CashFlow(amount=curr_val, date=val_date))

        return cfs

    @staticmethod
    def cash_flows_inr(asset: dict, transactions: list, rate: float, mode: str = "lifetime", valuation_date: datetime = None) -> list:
        val_date = valuation_date or datetime.now(timezone.utc)
        holding_type = asset.get('holding_type', 'investment')
        cfs = []

        sorted_txs = sorted(transactions, key=lambda x: (x['date'], x.get('created_at', x['date'])))

        if mode == "active" and holding_type == "investment" and any(tx['type'] == 'SELL' for tx in transactions):
            fifo_inr = FifoService.calculate_in_inr(transactions, rate)
            holdings = fifo_inr.holdings
            if not holdings: return []

            for lot in holdings:
                cfs.append(CashFlow(amount=-(lot.remaining_units * lot.buy_price_inr), date=lot.date))

            oldest_active_date = min(lot.date for lot in holdings)
            for tx in transactions:
                if tx['type'] == 'DIVIDEND' and tx['date'] >= oldest_active_date:
                    tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else rate
                    amt = tx['price_per_unit'] * (tx['units'] if tx['units'] > 0 else 1.0)
                    cfs.append(CashFlow(amount=amt * tx_rate, date=tx['date']))
        else:
            for tx in sorted_txs:
                cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
                tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else rate
                amt = tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0) * tx_rate
                raw_u = tx.get('raw_type', tx['type']).upper()

                if cfg.cash_direction == CashDirection.OUTFLOW:
                    cfs.append(CashFlow(amount=-amt, date=tx['date']))
                elif cfg.cash_direction in [CashDirection.INFLOW, CashDirection.INTERNAL_ACCRUAL] or tx['type'] == 'DIVIDEND' or 'DIVIDEND' in raw_u:
                    cfs.append(CashFlow(amount=amt, date=tx['date']))

        curr_val_inr = PortfolioService.current_value_inr(asset, transactions, rate)
        if curr_val_inr > 0 and not PortfolioService.is_sold_off(asset, transactions):
            cfs.append(CashFlow(amount=curr_val_inr, date=val_date))

        return cfs

    @staticmethod
    def xirr(asset: dict, transactions: list, mode: str = "lifetime", valuation_date: datetime = None) -> float:
        cfs = PortfolioService.cash_flows(asset, transactions, mode, valuation_date)
        return XirrService.calculate_xirr(cfs)

    @staticmethod
    def xirr_inr(asset: dict, transactions: list, rate: float, mode: str = "lifetime", valuation_date: datetime = None) -> float:
        cfs = PortfolioService.cash_flows_inr(asset, transactions, rate, mode, valuation_date)
        return XirrService.calculate_xirr(cfs)

    @staticmethod
    def recency_status(transactions: list) -> str:
        buy_txs = [tx for tx in transactions if tx['type'] == 'BUY' or TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), tx.get('asset_holding_type', 'investment')).cash_direction == CashDirection.OUTFLOW]
        if not buy_txs:
            return InvestmentRecencyStatus.NEVER

        last_tx = max(buy_txs, key=lambda x: x['date'])
        now_dt = datetime.now(timezone.utc)
        days = (now_dt - last_tx['date']).days

        if days <= 30: return InvestmentRecencyStatus.ACTIVE
        if days <= 90: return InvestmentRecencyStatus.MODERATE
        return InvestmentRecencyStatus.DORMANT

    @staticmethod
    def lifetime_invested(asset: dict, transactions: list) -> float:
        holding_type = asset.get('holding_type', 'investment')
        total = 0.0
        for tx in transactions:
            cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
            if cfg.cash_direction == CashDirection.OUTFLOW:
                total += tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0)
        return total

    @staticmethod
    def lifetime_invested_inr(asset: dict, transactions: list, rate: float) -> float:
        holding_type = asset.get('holding_type', 'investment')
        total = 0.0
        for tx in transactions:
            cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
            if cfg.cash_direction == CashDirection.OUTFLOW:
                tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else rate
                total += tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0) * tx_rate
        return total

    @staticmethod
    def lifetime_retrieved(asset: dict, transactions: list) -> float:
        holding_type = asset.get('holding_type', 'investment')
        total = 0.0
        for tx in transactions:
            cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
            if cfg.cash_direction in [CashDirection.INFLOW, CashDirection.INTERNAL_ACCRUAL] or tx['type'] == 'DIVIDEND' or 'DIVIDEND' in tx.get('raw_type', tx['type']).upper():
                total += tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0)
        return total

    @staticmethod
    def lifetime_retrieved_inr(asset: dict, transactions: list, rate: float) -> float:
        holding_type = asset.get('holding_type', 'investment')
        total = 0.0
        for tx in transactions:
            cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
            if cfg.cash_direction in [CashDirection.INFLOW, CashDirection.INTERNAL_ACCRUAL] or tx['type'] == 'DIVIDEND' or 'DIVIDEND' in tx.get('raw_type', tx['type']).upper():
                tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else rate
                total += tx['price_per_unit'] * (tx['units'] if cfg.is_unit_based else 1.0) * tx_rate
        return total

    @staticmethod
    def lifetime_dividend(asset: dict, transactions: list) -> float:
        total = 0.0
        for tx in transactions:
            if tx['type'] == 'DIVIDEND' or 'DIVIDEND' in tx.get('raw_type', tx['type']).upper():
                total += tx['price_per_unit'] * (tx['units'] if tx['units'] > 0 else 1.0)
        return total

    @staticmethod
    def lifetime_dividend_inr(asset: dict, transactions: list, rate: float) -> float:
        total = 0.0
        for tx in transactions:
            if tx['type'] == 'DIVIDEND' or 'DIVIDEND' in tx.get('raw_type', tx['type']).upper():
                tx_rate = tx.get('inr_exchange_rate') if tx.get('inr_exchange_rate') is not None else rate
                total += tx['price_per_unit'] * (tx['units'] if tx['units'] > 0 else 1.0) * tx_rate
        return total

    @staticmethod
    def transaction_counts(transactions: list, holding_type: str = "investment") -> dict:
        buy_count = 0
        sell_count = 0
        for tx in transactions:
            cfg = TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), holding_type)
            if cfg.cash_direction == CashDirection.OUTFLOW:
                buy_count += 1
            elif cfg.cash_direction == CashDirection.INFLOW:
                sell_count += 1
        total = buy_count + sell_count
        buy_pct = (buy_count / total * 100.0) if total > 0 else 100.0
        discipline_text = f"{buy_count} Buys / {sell_count} Sells"
        return {
            'buy_count': buy_count,
            'sell_count': sell_count,
            'total': total,
            'buy_pct': buy_pct,
            'discipline_text': discipline_text
        }

    @staticmethod
    def inception_date_info(transactions: list) -> dict:
        outflows = [tx for tx in transactions if tx['type'] == 'BUY' or TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), tx.get('asset_holding_type', 'investment')).cash_direction == CashDirection.OUTFLOW]
        if not outflows:
            return {'date': None, 'text': 'N/A'}
        first_tx = min(outflows, key=lambda x: x['date'])
        now_dt = datetime.now(timezone.utc)
        days = (now_dt - first_tx['date']).days
        date_str = first_tx['date'].strftime('%b %d, %Y')
        if days >= 365:
            duration = f"({days // 365} yr, {(days % 365) // 30} mo ago)"
        elif days >= 30:
            duration = f"({days // 30} mo ago)"
        else:
            duration = f"({days} days ago)"
        return {'date': first_tx['date'], 'text': f"{date_str} {duration}"}

    @staticmethod
    def last_invested_date_info(transactions: list) -> dict:
        outflows = [tx for tx in transactions if tx['type'] == 'BUY' or TransactionTypeRegistry.config(tx.get('raw_type', tx['type']), tx.get('asset_holding_type', 'investment')).cash_direction == CashDirection.OUTFLOW]
        if not outflows:
            return {'date': None, 'text': 'Never Invested'}
        last_tx = max(outflows, key=lambda x: x['date'])
        date_str = last_tx['date'].strftime('%b %d, %Y')
        return {'date': last_tx['date'], 'text': date_str}

    @staticmethod
    def total_interest_accrued(asset: dict, transactions: list) -> float:
        total = 0.0
        holding_type = asset.get('holding_type', 'investment')
        for tx in transactions:
            raw = tx.get('raw_type', tx['type']).upper()
            if 'INTEREST' in raw or 'BONUS' in raw:
                total += tx['price_per_unit'] * (tx['units'] if tx['units'] > 0 else 1.0)
        return total

