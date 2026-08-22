from flask import Blueprint, render_template, request
from app.repositories.asset_repository import AssetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.user_repository import UserRepository
from app.services.portfolio_service import PortfolioService
from app.services.fifo_service import FifoService

tax_planner_bp = Blueprint('tax_planner', __name__)

@tax_planner_bp.route('/tax-planner')
def index():
    user = UserRepository.get_user()
    slab_rate = user['tax_slab_rate'] if user else 0.30

    all_assets = AssetRepository.get_all()
    categories = CategoryRepository.get_all()
    currencies = CurrencyRepository.get_all()

    realized_stcg_inr = 0.0
    realized_ltcg_inr = 0.0
    realized_slab_inr = 0.0

    realized_tax_inr = 0.0
    unrealized_tax_inr = 0.0

    active_holding_lots = []
    realized_trades = []

    for asset in all_assets:
        txs = TransactionRepository.get_by_asset(asset['id'])
        cat = next((c for c in categories if c['id'] == asset['category_id']), None)
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies) if cat else 1.0

        tax_res = FifoService.calculate_tax(asset, txs, rate, slab_rate=slab_rate)

        realized_stcg_inr += tax_res.total_realized_stcg_gains
        realized_ltcg_inr += tax_res.total_realized_ltcg_gains
        realized_slab_inr += tax_res.total_realized_slab_gains
        realized_tax_inr += tax_res.total_realized_tax

        unrealized_tax_inr += tax_res.total_unrealized_tax

        for lot in tax_res.active_lots:
            active_holding_lots.append({'asset': asset, 'lot': lot})

        for trade in tax_res.realized_trades_current_fy:
            realized_trades.append({'asset': asset, 'trade': trade})

    return render_template(
        'tax_planner.html',
        slab_rate=slab_rate,
        realized_stcg_inr=realized_stcg_inr,
        realized_ltcg_inr=realized_ltcg_inr,
        realized_slab_inr=realized_slab_inr,
        realized_tax_inr=realized_tax_inr,
        unrealized_tax_inr=unrealized_tax_inr,
        active_lots=active_holding_lots,
        realized_trades=realized_trades
    )
