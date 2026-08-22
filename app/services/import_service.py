import csv
import io
from datetime import datetime, timezone
from app.repositories.asset_repository import AssetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.utils.date_utils import parse_iso_date

class ImportService:
    @staticmethod
    def match_asset(query_str: str, assets: list) -> dict:
        if not query_str: return None
        clean_q = query_str.strip().lower()

        # 1. Exact Ticker Match
        for a in assets:
            if a.get('ticker') and a['ticker'].strip().lower() == clean_q:
                return a

        # 2. Exact Name Match
        for a in assets:
            if a['name'].strip().lower() == clean_q:
                return a

        # 3. Alias Match
        for a in assets:
            for alias in a.get('aliases', []):
                if alias.strip().lower() == clean_q:
                    return a

        # 4. Partial Name Match
        for a in assets:
            if clean_q in a['name'].strip().lower() or a['name'].strip().lower() in clean_q:
                return a

        return None

    @staticmethod
    def parse_csv_transactions(csv_content: str) -> list:
        f = io.StringIO(csv_content)
        reader = csv.DictReader(f)
        results = []

        for row in reader:
            # Flexible field mapping
            asset_identifier = row.get('Asset') or row.get('Symbol') or row.get('Ticker') or row.get('Name') or ''
            tx_type = (row.get('Type') or row.get('Transaction') or row.get('Action') or 'BUY').upper()
            date_str = row.get('Date') or row.get('Trade Date') or ''
            units_str = row.get('Units') or row.get('Quantity') or row.get('Qty') or '1.0'
            price_str = row.get('Price') or row.get('Price/Unit') or row.get('Rate') or row.get('Amount') or '0.0'
            notes = row.get('Notes') or row.get('Description') or row.get('Memo') or ''

            try:
                units = float(units_str.replace(',', ''))
            except Exception:
                units = 1.0

            try:
                price = float(price_str.replace(',', '').replace('$', '').replace('₹', ''))
            except Exception:
                price = 0.0

            dt = parse_iso_date(date_str)

            results.append({
                'asset_identifier': asset_identifier,
                'type': tx_type,
                'date': dt,
                'units': units,
                'price_per_unit': price,
                'notes': notes
            })

        return results
