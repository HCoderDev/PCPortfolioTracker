from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.snapshot_repository import SnapshotRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.portfolio_service import PortfolioService

snapshots_bp = Blueprint('snapshots', __name__)

@snapshots_bp.route('/snapshots')
def index():
    snapshots = SnapshotRepository.get_all()
    return render_template('snapshots.html', snapshots=snapshots)

@snapshots_bp.route('/snapshots/<int:snap_id>')
def detail(snap_id: int):
    snapshot = SnapshotRepository.get_by_id(snap_id)
    if not snapshot:
        flash("Snapshot not found.", "danger")
        return redirect(url_for('snapshots.index'))
    return render_template('snapshot_detail.html', snapshot=snapshot)

@snapshots_bp.route('/snapshots/create', methods=['POST'])
def create_snapshot():
    note = request.form.get('note', '').strip()
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()

    total_inv_inr = 0.0
    total_val_inr = 0.0
    category_snapshots = []

    for cat in categories:
        cat_assets = [a for a in all_assets if a['category_id'] == cat['id']]
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies)
        cat_inv = 0.0
        cat_val = 0.0
        cat_inv_inr = 0.0
        cat_val_inr = 0.0
        asset_snaps = []

        for asset in cat_assets:
            txs = TransactionRepository.get_by_asset(asset['id'])
            if PortfolioService.is_sold_off(asset, txs): continue

            inv = PortfolioService.invested_value(asset, txs)
            val = PortfolioService.current_value(asset, txs)
            inv_inr = PortfolioService.invested_value_inr(asset, txs, rate)
            val_inr = PortfolioService.current_value_inr(asset, txs, rate)
            units = PortfolioService.total_units(txs, asset.get('holding_type', 'investment'))

            cat_inv += inv
            cat_val += val
            cat_inv_inr += inv_inr
            cat_val_inr += val_inr

            asset_snaps.append({
                'asset_name': asset['name'],
                'units': units,
                'current_price': asset['current_price'],
                'invested_value': inv,
                'current_value': val,
                'invested_value_inr': inv_inr,
                'current_value_inr': val_inr
            })

        total_inv_inr += cat_inv_inr
        total_val_inr += cat_val_inr

        category_snapshots.append({
            'category_name': cat['name'],
            'currency_code': cat['currency_code'],
            'invested_value': cat_inv,
            'current_value': cat_val,
            'invested_value_inr': cat_inv_inr,
            'current_value_inr': cat_val_inr,
            'exchange_rate_to_inr': rate,
            'assets': asset_snaps
        })

    new_id = SnapshotRepository.create_snapshot(note, total_inv_inr, total_val_inr, category_snapshots)
    flash("Portfolio Snapshot saved successfully.", "success")
    return redirect(url_for('snapshots.detail', snap_id=new_id))
