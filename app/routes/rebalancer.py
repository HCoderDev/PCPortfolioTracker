from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.portfolio_service import PortfolioService

rebalancer_bp = Blueprint('rebalancer', __name__)

@rebalancer_bp.route('/rebalancer')
def index():
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()

    total_portfolio_inr = 0.0
    category_rebalance_rows = []

    for cat in categories:
        cat_assets = [a for a in all_assets if a['category_id'] == cat['id']]
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies)
        cat_val_inr = 0.0

        for asset in cat_assets:
            txs = TransactionRepository.get_by_asset(asset['id'])
            if PortfolioService.is_sold_off(asset, txs): continue
            cat_val_inr += PortfolioService.current_value_inr(asset, txs, rate)

        total_portfolio_inr += cat_val_inr

        category_rebalance_rows.append({
            'category': cat,
            'current_val_inr': cat_val_inr,
            'target_pct': cat['target_allocation'],
            'rate': rate
        })

    targets_sum = sum(c['target_pct'] for c in category_rebalance_rows)

    for row in category_rebalance_rows:
        actual_pct = (row['current_val_inr'] / total_portfolio_inr * 100.0) if total_portfolio_inr > 0 else 0.0
        drift_pct = actual_pct - row['target_pct']
        target_val_inr = total_portfolio_inr * (row['target_pct'] / 100.0)
        rebalance_action_inr = target_val_inr - row['current_val_inr']  # positive = BUY, negative = SELL

        row['actual_pct'] = actual_pct
        row['drift_pct'] = drift_pct
        row['target_val_inr'] = target_val_inr
        row['rebalance_action_inr'] = rebalance_action_inr
        row['rebalance_action_local'] = rebalance_action_inr / row['rate'] if row['rate'] > 0 else rebalance_action_inr

    return render_template(
        'rebalancer.html',
        categories=category_rebalance_rows,
        total_portfolio_inr=total_portfolio_inr,
        targets_sum=targets_sum
    )

@rebalancer_bp.route('/rebalancer/config', methods=['POST'])
def save_config():
    categories = CategoryRepository.get_all()
    for cat in categories:
        key = f"target_{cat['id']}"
        if key in request.form:
            try:
                new_target = float(request.form[key])
                CategoryRepository.update(cat['id'], {
                    'name': cat['name'],
                    'currency_code': cat['currency_code'],
                    'last_inr_exchange_rate': cat['last_inr_exchange_rate'],
                    'convert_to_inr': cat['convert_to_inr'],
                    'is_individual_equity': cat['is_individual_equity'],
                    'target_allocation': new_target,
                    'ltcg_threshold_months': cat['ltcg_threshold_months'],
                    'passive_transaction_types_raw': cat['passive_transaction_types_raw']
                })
            except ValueError:
                pass
    flash("Target allocation percentages saved.", "success")
    return redirect(url_for('rebalancer.index'))
