from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.currency_repository import CurrencyRepository
from app.services.portfolio_service import PortfolioService

categories_bp = Blueprint('categories', __name__)

@categories_bp.route('/categories')
def list_categories():
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()

    category_cards = []
    total_portfolio_val_inr = 0.0

    for cat in categories:
        cat_assets = [a for a in all_assets if a['category_id'] == cat['id']]
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies)

        cat_invested = 0.0
        cat_value = 0.0
        cat_value_inr = 0.0

        for asset in cat_assets:
            txs = TransactionRepository.get_by_asset(asset['id'])
            if PortfolioService.is_sold_off(asset, txs): continue

            inv = PortfolioService.invested_value(asset, txs)
            val = PortfolioService.current_value(asset, txs)
            val_inr = PortfolioService.current_value_inr(asset, txs, rate)

            cat_invested += inv
            cat_value += val
            cat_value_inr += val_inr

        total_portfolio_val_inr += cat_value_inr

        category_cards.append({
            'category': cat,
            'assets_count': len(cat_assets),
            'invested': cat_invested,
            'current_value': cat_value,
            'current_value_inr': cat_value_inr,
            'gain_loss': cat_value - cat_invested,
            'gain_loss_pct': ((cat_value - cat_invested) / cat_invested * 100.0) if cat_invested > 0 else 0.0,
            'rate': rate
        })

    for card in category_cards:
        card['actual_allocation_pct'] = (card['current_value_inr'] / total_portfolio_val_inr * 100.0) if total_portfolio_val_inr > 0 else 0.0

    return render_template('categories/list.html', category_cards=category_cards, currencies=currencies)

@categories_bp.route('/categories/<int:cat_id>')
def category_detail(cat_id: int):
    category = CategoryRepository.get_by_id(cat_id)
    if not category:
        flash("Category not found.", "danger")
        return redirect(url_for('categories.list_categories'))

    subcategories = CategoryRepository.get_subcategories(cat_id)
    cat_assets = AssetRepository.get_by_category(cat_id)
    currencies = CurrencyRepository.get_all()
    rate = PortfolioService.current_inr_exchange_rate(category, currencies)

    asset_rows = []
    tot_inv = 0.0
    tot_val = 0.0

    for asset in cat_assets:
        txs = TransactionRepository.get_by_asset(asset['id'])
        inv = PortfolioService.invested_value(asset, txs)
        val = PortfolioService.current_value(asset, txs)
        units = PortfolioService.total_units(txs, asset.get('holding_type', 'investment'))

        tot_inv += inv
        tot_val += val

        asset_rows.append({
            'asset': asset,
            'units': units,
            'invested': inv,
            'current_value': val,
            'gain_loss': val - inv,
            'gain_loss_pct': ((val - inv) / inv * 100.0) if inv > 0 else 0.0,
            'is_sold_off': PortfolioService.is_sold_off(asset, txs)
        })

    # Asset Level Allocation
    asset_allocations = []
    for row in asset_rows:
        if not row['is_sold_off'] and row['current_value'] > 0:
            asset_allocations.append({
                'label': row['asset']['name'],
                'value': row['current_value'],
                'pct': (row['current_value'] / tot_val * 100.0) if tot_val > 0 else 0.0
            })
    asset_allocations.sort(key=lambda x: x['value'], reverse=True)

    # Subcategory Level Allocation
    subcat_map = {}
    subcat_lookup = {sc['id']: sc['name'] for sc in subcategories}

    for row in asset_rows:
        if not row['is_sold_off'] and row['current_value'] > 0:
            sc_id = row['asset'].get('subcategory_id')
            sc_name = subcat_lookup.get(sc_id, 'Unassigned') if sc_id else 'Unassigned'
            subcat_map[sc_name] = subcat_map.get(sc_name, 0.0) + row['current_value']

    subcategory_allocations = [
        {'label': k, 'value': v, 'pct': (v / tot_val * 100.0) if tot_val > 0 else 0.0}
        for k, v in subcat_map.items()
    ]
    subcategory_allocations.sort(key=lambda x: x['value'], reverse=True)

    return render_template(
        'categories/detail.html',
        category=category,
        subcategories=subcategories,
        assets=asset_rows,
        tot_inv=tot_inv,
        tot_val=tot_val,
        tot_gain=tot_val - tot_inv,
        tot_gain_pct=((tot_val - tot_inv) / tot_inv * 100.0) if tot_inv > 0 else 0.0,
        rate=rate,
        asset_allocations=asset_allocations,
        subcategory_allocations=subcategory_allocations
    )

@categories_bp.route('/categories/add', methods=['POST'])
def add_category():
    selected_passive = request.form.getlist('passive_types')
    raw_passive = '|||'.join([p.strip().upper() for p in selected_passive if p.strip()])

    track_updated = bool(request.form.get('track_last_updated'))
    last_updated = None
    if track_updated:
        date_str = request.form.get('last_updated_date')
        if date_str:
            try:
                last_updated = datetime.fromisoformat(date_str)
            except ValueError:
                last_updated = datetime.now()
        else:
            last_updated = datetime.now()

    data = {
        'name': request.form.get('name', '').strip(),
        'currency_code': request.form.get('currency_code', 'INR').upper(),
        'last_inr_exchange_rate': float(request.form.get('last_inr_exchange_rate', 1.0) or 1.0),
        'convert_to_inr': bool(request.form.get('convert_to_inr')),
        'is_individual_equity': bool(request.form.get('is_individual_equity')),
        'target_allocation': float(request.form.get('target_allocation', 0.0) or 0.0),
        'ltcg_threshold_months': int(request.form.get('ltcg_threshold_months', 12) or 12),
        'passive_transaction_types_raw': raw_passive,
        'last_updated_date': last_updated
    }
    cat_id = CategoryRepository.create(data)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'status': 'success', 'category_id': cat_id}
    flash(f"Category '{data['name']}' created.", "success")
    return redirect(url_for('categories.list_categories'))

@categories_bp.route('/categories/edit/<int:cat_id>', methods=['POST'])
def edit_category(cat_id: int):
    selected_passive = request.form.getlist('passive_types')
    raw_passive = '|||'.join([p.strip().upper() for p in selected_passive if p.strip()])

    track_updated = bool(request.form.get('track_last_updated'))
    last_updated = None
    if track_updated:
        date_str = request.form.get('last_updated_date')
        if date_str:
            try:
                last_updated = datetime.fromisoformat(date_str)
            except ValueError:
                last_updated = datetime.now()
        else:
            last_updated = datetime.now()

    data = {
        'name': request.form.get('name', '').strip(),
        'currency_code': request.form.get('currency_code', 'INR').upper(),
        'last_inr_exchange_rate': float(request.form.get('last_inr_exchange_rate', 1.0) or 1.0),
        'convert_to_inr': bool(request.form.get('convert_to_inr')),
        'is_individual_equity': bool(request.form.get('is_individual_equity')),
        'target_allocation': float(request.form.get('target_allocation', 0.0) or 0.0),
        'ltcg_threshold_months': int(request.form.get('ltcg_threshold_months', 12) or 12),
        'passive_transaction_types_raw': raw_passive,
        'last_updated_date': last_updated
    }
    CategoryRepository.update(cat_id, data)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'status': 'success', 'category_id': cat_id}
    flash("Category updated.", "success")
    return redirect(url_for('categories.category_detail', cat_id=cat_id))

@categories_bp.route('/categories/allowed-passive-types/<int:cat_id>')
def allowed_passive_types(cat_id: int):
    cat = CategoryRepository.get_by_id(cat_id)
    cat_name = cat['name'] if cat else ''
    allowed = CategoryRepository.allowed_passive_transaction_types(cat_id, cat_name)
    current_passive = list(cat['passive_transaction_types']) if cat else []
    return jsonify({'allowed': allowed, 'current': current_passive})

@categories_bp.route('/categories/delete/<int:cat_id>', methods=['POST'])
def delete_category(cat_id: int):
    CategoryRepository.delete(cat_id)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'status': 'success'}
    flash("Category deleted.", "success")
    return redirect(url_for('categories.list_categories'))

@categories_bp.route('/subcategories/add', methods=['POST'])
def add_subcategory():
    cat_id = int(request.form.get('category_id'))
    name = request.form.get('name', '').strip()
    if name:
        CategoryRepository.create_subcategory(cat_id, name)
        flash(f"Sub-category '{name}' added.", "success")
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'status': 'success'}
    return redirect(url_for('categories.category_detail', cat_id=cat_id))

@categories_bp.route('/categories/update-passive-rules/<int:cat_id>', methods=['POST'])
def update_passive_rules(cat_id: int):
    category = CategoryRepository.get_by_id(cat_id)
    if not category:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'status': 'error', 'message': 'Category not found'}, 404
        flash("Category not found.", "danger")
        return redirect(url_for('categories.list_categories'))

    selected_types = request.form.getlist('passive_types')
    raw_str = '|||'.join([p.strip().upper() for p in selected_types if p.strip()])

    data = {
        'name': category['name'],
        'currency_code': category['currency_code'],
        'last_inr_exchange_rate': category['last_inr_exchange_rate'],
        'convert_to_inr': category['convert_to_inr'],
        'is_individual_equity': category['is_individual_equity'],
        'target_allocation': category['target_allocation'],
        'ltcg_threshold_months': category['ltcg_threshold_months'],
        'passive_transaction_types_raw': raw_str,
        'last_updated_date': category['last_updated_date']
    }
    CategoryRepository.update(cat_id, data)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return {'status': 'success', 'category_id': cat_id}
    flash("Passive income rules updated.", "success")
    return redirect(url_for('categories.category_detail', cat_id=cat_id))
