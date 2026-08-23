from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.currency_repository import CurrencyRepository
from app.services.portfolio_service import PortfolioService
from app.services.fifo_service import FifoService
from app.services.xirr_service import XirrService
from app.utils.date_utils import parse_iso_date

def calculate_category_growth_timeline(cat_assets, rate=1.0):
    all_txs = []
    asset_price_map = {}
    for asset in cat_assets:
        asset_id = asset['id']
        asset_price_map[asset_id] = float(asset.get('current_price', 0.0) or 0.0)
        txs = TransactionRepository.get_by_asset(asset_id)
        for t in txs:
            t_date = t.get('date')
            if not t_date: continue
            raw_type = (t.get('raw_type') or t.get('type') or '').upper()
            all_txs.append({
                'date': t_date,
                'raw_type': raw_type,
                'units': float(t.get('units', 0.0) or 0.0),
                'price_per_unit': float(t.get('price_per_unit', 0.0) or 0.0),
                'asset_id': asset_id,
                'id': t.get('id', 0)
            })

    if not all_txs:
        return []

    all_txs.sort(key=lambda x: (x['date'], x['id']))
    ledgers = {}
    timeline_points = []

    for tx in all_txs:
        aid = tx['asset_id']
        if aid not in ledgers:
            ledgers[aid] = {'buy_lots': [], 'current_units': 0.0}
        
        ledger = ledgers[aid]
        raw = tx['raw_type']
        units = tx['units']
        price = tx['price_per_unit']

        if raw in ['BUY', 'DEPOSIT', 'CONTRIBUTION', 'EMPLOYEE_CONTRIBUTION', 'EMPLOYER_CONTRIBUTION']:
            ledger['buy_lots'].append({'remaining_units': units, 'buy_price': price})
            ledger['current_units'] += units
        elif raw in ['SELL', 'WITHDRAWAL', 'MATURITY', 'SURRENDER']:
            units_to_sell = units
            ledger['current_units'] -= units
            for lot in ledger['buy_lots']:
                if units_to_sell <= 0: break
                if lot['remaining_units'] > 0:
                    taken = min(units_to_sell, lot['remaining_units'])
                    lot['remaining_units'] -= taken
                    units_to_sell -= taken

        tot_invested = 0.0
        tot_val = 0.0

        for a_id, leg in ledgers.items():
            curr_p = asset_price_map.get(a_id, 0.0)
            inv = sum(l['remaining_units'] * l['buy_price'] for l in leg['buy_lots'] if l['remaining_units'] > 0)
            val = max(0.0, leg['current_units']) * curr_p
            tot_invested += inv
            tot_val += val

        dt_str = tx['date'].strftime('%d-%m-%Y') if hasattr(tx['date'], 'strftime') else str(tx['date'])[:10]
        dt_iso = tx['date'].strftime('%Y-%m-%d') if hasattr(tx['date'], 'strftime') else str(tx['date'])[:10]
        timeline_points.append({
            'date': dt_str,
            'date_iso': dt_iso,
            'invested': round(tot_invested * rate, 2),
            'value': round(tot_val * rate, 2)
        })

    today_now = datetime.now()
    today_str = today_now.strftime('%d-%m-%Y')
    today_iso = today_now.strftime('%Y-%m-%d')
    if timeline_points and timeline_points[-1]['date'] != today_str:
        timeline_points.append({
            'date': today_str,
            'date_iso': today_iso,
            'invested': timeline_points[-1]['invested'],
            'value': timeline_points[-1]['value']
        })

    return timeline_points

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
    tot_realized_pl = 0.0
    tot_lifetime_invested = 0.0
    tot_lifetime_retrieved = 0.0
    tot_lifetime_dividend = 0.0

    all_lifetime_cfs = []
    all_active_cfs = []

    for asset in cat_assets:
        txs = TransactionRepository.get_by_asset(asset['id'])
        inv = PortfolioService.invested_value(asset, txs)
        val = PortfolioService.current_value(asset, txs)
        units = PortfolioService.total_units(txs, asset.get('holding_type', 'investment'))
        is_sold_off = PortfolioService.is_sold_off(asset, txs)

        fifo_res = FifoService.calculate(txs)
        realized_pl = fifo_res.realized_profit_loss
        div = PortfolioService.lifetime_dividend(asset, txs)

        tot_inv += inv
        tot_val += val
        tot_realized_pl += realized_pl
        tot_lifetime_invested += fifo_res.lifetime_invested
        tot_lifetime_retrieved += fifo_res.lifetime_retrieved
        tot_lifetime_dividend += div

        asset_lifetime_cfs = PortfolioService.cash_flows(asset, txs, mode="lifetime")
        all_lifetime_cfs.extend(asset_lifetime_cfs)

        if not is_sold_off:
            asset_active_cfs = PortfolioService.cash_flows(asset, txs, mode="active")
            all_active_cfs.extend(asset_active_cfs)

        asset_rows.append({
            'asset': asset,
            'units': units,
            'invested': inv,
            'current_value': val,
            'gain_loss': val - inv,
            'gain_loss_pct': ((val - inv) / inv * 100.0) if inv > 0 else 0.0,
            'realized_pl': realized_pl,
            'dividend': div,
            'is_sold_off': is_sold_off
        })

    tot_unrealized = tot_val - tot_inv
    tot_total_pl = tot_unrealized + tot_realized_pl + tot_lifetime_dividend
    lifetime_xirr = XirrService.calculate_xirr(all_lifetime_cfs)
    active_xirr = XirrService.calculate_xirr(all_active_cfs)

    active_count = len([r for r in asset_rows if not r['is_sold_off']])
    sold_count = len([r for r in asset_rows if r['is_sold_off']])

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

    growth_timeline = calculate_category_growth_timeline(cat_assets, rate)

    return render_template(
        'categories/detail.html',
        category=category,
        subcategories=subcategories,
        assets=asset_rows,
        tot_inv=tot_inv,
        tot_val=tot_val,
        tot_unrealized=tot_unrealized,
        tot_realized_pl=tot_realized_pl,
        tot_total_pl=tot_total_pl,
        tot_lifetime_invested=tot_lifetime_invested,
        tot_lifetime_retrieved=tot_lifetime_retrieved,
        tot_lifetime_dividend=tot_lifetime_dividend,
        lifetime_xirr=lifetime_xirr,
        active_xirr=active_xirr,
        active_count=active_count,
        sold_count=sold_count,
        tot_gain=tot_unrealized,
        tot_gain_pct=((tot_unrealized) / tot_inv * 100.0) if tot_inv > 0 else 0.0,
        rate=rate,
        asset_allocations=asset_allocations,
        subcategory_allocations=subcategory_allocations,
        growth_timeline=growth_timeline
    )

@categories_bp.route('/categories/update-last-updated/<int:cat_id>', methods=['POST'])
def update_last_updated(cat_id: int):
    category = CategoryRepository.get_by_id(cat_id)
    if not category:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return {'status': 'error', 'message': 'Category not found'}, 404
        flash("Category not found.", "danger")
        return redirect(url_for('categories.list_categories'))

    action = request.form.get('action', 'today')
    dt = None

    if action == 'today':
        dt = datetime.now()
    elif action == 'custom':
        date_str = request.form.get('last_updated_date')
        if date_str:
            dt = parse_iso_date(date_str)
        else:
            dt = datetime.now()
    elif action == 'clear':
        dt = None

    CategoryRepository.update_last_updated_date(cat_id, dt)

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        updated_str = dt.strftime('%d-%m-%Y %I:%M %p') if dt else None
        return {'status': 'success', 'category_id': cat_id, 'last_updated_date': updated_str}

    flash("Category data updated timestamp updated.", "success")
    return redirect(url_for('categories.category_detail', cat_id=cat_id))

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
