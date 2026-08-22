import math
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.asset_repository import AssetRepository

class StockAnalysisService:
    @staticmethod
    def calculate_dcf(cmp: float, starting_fcf: float, growth_rate: float, discount_rate: float, terminal_growth: float, shares: float) -> dict:
        """
        Discounted Cash Flow 10-Year Valuation Model.
        """
        if shares <= 0:
            return {'intrinsic_value_per_share': 0.0, 'margin_of_safety_pct': 0.0}

        g = growth_rate / 100.0
        d = discount_rate / 100.0
        tg = terminal_growth / 100.0

        pv_fcf_sum = 0.0
        current_fcf = starting_fcf

        for yr in range(1, 11):
            current_fcf *= (1.0 + g)
            discount_factor = math.pow(1.0 + d, yr)
            pv_fcf_sum += (current_fcf / discount_factor)

        terminal_value = (current_fcf * (1.0 + tg)) / max(0.001, d - tg)
        pv_terminal_value = terminal_value / math.pow(1.0 + d, 10)

        total_intrinsic_value = pv_fcf_sum + pv_terminal_value
        value_per_share = total_intrinsic_value / shares

        margin_of_safety = ((value_per_share - cmp) / value_per_share * 100.0) if value_per_share > 0 else 0.0

        return {
            'pv_fcf_sum': pv_fcf_sum,
            'pv_terminal_value': pv_terminal_value,
            'total_intrinsic_value': total_intrinsic_value,
            'intrinsic_value_per_share': value_per_share,
            'margin_of_safety_pct': margin_of_safety
        }

    @staticmethod
    def process_stock_split(asset_id: int, split_ratio_new: float, split_ratio_old: float):
        """
        Applies a Stock Split / Reverse Split to all historical transactions of an asset.
        Multiplier = split_ratio_new / split_ratio_old.
        Units are multiplied by Multiplier; Price per unit is divided by Multiplier.
        """
        if split_ratio_old <= 0 or split_ratio_new <= 0: return

        multiplier = split_ratio_new / split_ratio_old
        txs = TransactionRepository.get_by_asset(asset_id)
        asset = AssetRepository.get_by_id(asset_id)

        for tx in txs:
            if tx['type'] in ['BUY', 'SELL']:
                new_units = tx['units'] * multiplier
                new_price = tx['price_per_unit'] / multiplier
                TransactionRepository.update(tx['id'], {
                    'asset_id': tx['asset_id'],
                    'broker_id': tx['broker_id'],
                    'type': tx['type'],
                    'raw_type': tx['raw_type'],
                    'units': new_units,
                    'price_per_unit': new_price,
                    'date': tx['date'],
                    'inr_exchange_rate': tx['inr_exchange_rate'],
                    'notes': f"{tx['notes']} (Split {int(split_ratio_new)}:{int(split_ratio_old)})".strip()
                })

        if asset:
            new_cmp = asset['current_price'] / multiplier
            AssetRepository.update_price(asset_id, new_cmp)
