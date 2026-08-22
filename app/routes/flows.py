from flask import Blueprint, render_template, request
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.broker_repository import BrokerRepository
from app.repositories.currency_repository import CurrencyRepository
from app.services.portfolio_service import PortfolioService
from app.services.transaction_registry import TransactionTypeRegistry, CashDirection
from datetime import datetime, timezone

flows_bp = Blueprint('flows', __name__)

@flows_bp.route('/flows')
def index():
    all_txs = TransactionRepository.get_all()
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    brokers = BrokerRepository.get_all()
    currencies = CurrencyRepository.get_all()

    tx_years = [tx['date'].year for tx in all_txs if tx.get('date')]
    current_year = datetime.now(timezone.utc).year
    starting_year = min(tx_years) if tx_years else current_year
    available_years = sorted(list(set(tx_years + [current_year])), reverse=True)

    # Attach INR exchange rate to every transaction for multi-currency processing
    for tx in all_txs:
        cat = CategoryRepository.get_by_id(tx.get('category_id')) if tx.get('category_id') else None
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies) if cat else 1.0
        tx['inr_rate'] = tx.get('inr_exchange_rate') or rate
        tx['amount_inr'] = tx['price_per_unit'] * (tx['units'] if tx['type'] in ['BUY', 'SELL'] else 1.0) * tx['inr_rate']

    return render_template(
        'flows.html',
        transactions=all_txs,
        categories=categories,
        all_assets=all_assets,
        brokers=brokers,
        available_years=available_years,
        starting_year=starting_year,
        current_year=current_year
    )
