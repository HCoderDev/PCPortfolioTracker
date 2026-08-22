from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.asset_repository import AssetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.note_repository import NoteRepository
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.broker_repository import BrokerRepository
from app.repositories.analysis_repository import AnalysisRepository

from app.services.portfolio_service import PortfolioService, InvestmentRecencyStatus
from app.services.fifo_service import FifoService
from app.services.stock_analysis_service import StockAnalysisService
from app.utils.date_utils import parse_iso_date

assets_bp = Blueprint('assets', __name__)

@assets_bp.route('/assets')
def list_assets():
    categories = CategoryRepository.get_all()
    currencies = CurrencyRepository.get_all()
    all_assets = AssetRepository.get_all()

    # Query Params Filters
    filter_cat = request.args.get('category_id', type=int)
    filter_type = request.args.get('type', 'all')  # 'all', 'investment', 'contract'
    filter_recency = request.args.get('recency', 'all')  # 'all', 'active', 'moderate', 'dormant', 'never'
    hide_sold = request.args.get('hide_sold', '0')  # '0' or '1'
    search_q = request.args.get('q', '').strip().lower()
    sort_by = request.args.get('sort', 'name')

    asset_items = []
    for asset in all_assets:
        if filter_cat and asset['category_id'] != filter_cat:
            continue

        holding_type = asset.get('holding_type', 'investment')
        if filter_type == 'investment' and holding_type != 'investment':
            continue
        if filter_type == 'contract' and holding_type == 'investment':
            continue

        if search_q:
            t = (asset.get('ticker') or '').lower()
            n = asset['name'].lower()
            if search_q not in n and search_q not in t:
                continue

        txs = TransactionRepository.get_by_asset(asset['id'])
        is_sold_off = PortfolioService.is_sold_off(asset, txs)

        if hide_sold == '1' and is_sold_off:
            continue

        cat = CategoryRepository.get_by_id(asset['category_id']) if asset['category_id'] else None
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies) if cat else 1.0

        recency = PortfolioService.recency_status(txs)
        if filter_recency != 'all':
            if filter_recency == 'active' and recency != InvestmentRecencyStatus.ACTIVE: continue
            if filter_recency == 'moderate' and recency != InvestmentRecencyStatus.MODERATE: continue
            if filter_recency == 'dormant' and recency != InvestmentRecencyStatus.DORMANT: continue
            if filter_recency == 'never' and recency != InvestmentRecencyStatus.NEVER: continue

        units = PortfolioService.total_units(txs, holding_type)
        inv = PortfolioService.invested_value_inr(asset, txs, rate)
        val = PortfolioService.current_value_inr(asset, txs, rate)
        gain = val - inv
        gain_pct = (gain / inv * 100.0) if inv > 0 else 0.0

        asset_items.append({
            'asset': asset,
            'category_name': asset.get('category_name', ''),
            'currency_code': asset.get('category_currency', 'INR'),
            'rate': rate,
            'holding_type': holding_type,
            'recency': recency,
            'units': units,
            'invested_inr': inv,
            'current_value_inr': val,
            'gain_inr': gain,
            'gain_pct': gain_pct,
            'is_sold_off': is_sold_off
        })

    # Sorting
    if sort_by in ['value', 'value_desc']:
        asset_items.sort(key=lambda x: x['current_value_inr'], reverse=True)
    elif sort_by == 'value_asc':
        asset_items.sort(key=lambda x: x['current_value_inr'], reverse=False)
    elif sort_by in ['invested', 'invested_desc']:
        asset_items.sort(key=lambda x: x['invested_inr'], reverse=True)
    elif sort_by == 'invested_asc':
        asset_items.sort(key=lambda x: x['invested_inr'], reverse=False)
    elif sort_by in ['gain', 'gain_desc']:
        asset_items.sort(key=lambda x: x['gain_inr'], reverse=True)
    elif sort_by == 'gain_asc':
        asset_items.sort(key=lambda x: x['gain_inr'], reverse=False)
    elif sort_by == 'gain_pct_desc':
        asset_items.sort(key=lambda x: x['gain_pct'], reverse=True)
    elif sort_by == 'gain_pct_asc':
        asset_items.sort(key=lambda x: x['gain_pct'], reverse=False)
    elif sort_by == 'name_desc':
        asset_items.sort(key=lambda x: x['asset']['name'].lower(), reverse=True)
    else:  # 'name' or 'name_asc'
        asset_items.sort(key=lambda x: x['asset']['name'].lower())

    return render_template(
        'assets/list.html',
        assets=asset_items,
        categories=categories,
        filter_cat=filter_cat,
        filter_type=filter_type,
        filter_recency=filter_recency,
        hide_sold=hide_sold,
        search_q=search_q,
        sort_by=sort_by
    )

@assets_bp.route('/assets/<int:asset_id>')
def asset_detail(asset_id: int):
    asset = AssetRepository.get_by_id(asset_id)
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for('assets.list_assets'))

    txs = TransactionRepository.get_by_asset(asset_id)
    cat = CategoryRepository.get_by_id(asset['category_id']) if asset['category_id'] else None
    all_categories = CategoryRepository.get_all()
    currencies = CurrencyRepository.get_all()
    all_assets = AssetRepository.get_all()
    rate = PortfolioService.current_inr_exchange_rate(cat, currencies) if cat else 1.0

    holding_type = asset.get('holding_type', 'investment')
    units = PortfolioService.total_units(txs, holding_type)
    inv_local = PortfolioService.invested_value(asset, txs)
    val_local = PortfolioService.current_value(asset, txs)
    inv_inr = PortfolioService.invested_value_inr(asset, txs, rate)
    val_inr = PortfolioService.current_value_inr(asset, txs, rate)

    xirr_mode = request.args.get('xirr_mode', 'lifetime')
    xirr_val = PortfolioService.xirr_inr(asset, txs, rate, mode=xirr_mode)

    # Lifetime Cash Flows
    lifetime_inv_local = PortfolioService.lifetime_invested(asset, txs)
    lifetime_inv_inr = PortfolioService.lifetime_invested_inr(asset, txs, rate)
    lifetime_ret_local = PortfolioService.lifetime_retrieved(asset, txs)
    lifetime_ret_inr = PortfolioService.lifetime_retrieved_inr(asset, txs, rate)
    lifetime_div_local = PortfolioService.lifetime_dividend(asset, txs)
    lifetime_div_inr = PortfolioService.lifetime_dividend_inr(asset, txs, rate)

    # FIFO & Realized P&L
    fifo_inr = FifoService.calculate_in_inr(txs, rate)
    realized_pnl_inr = fifo_inr.realized_profit_loss
    unrealized_pnl_inr = val_inr - inv_inr
    total_gain_loss_inr = realized_pnl_inr + unrealized_pnl_inr
    overall_gain_loss_pct = (total_gain_loss_inr / lifetime_inv_inr * 100.0) if lifetime_inv_inr > 0 else 0.0

    # Allocations
    cat_total_val_inr = 0.0
    if cat:
        cat_assets = [a for a in all_assets if a.get('category_id') == cat['id']]
        for ca in cat_assets:
            ca_txs = TransactionRepository.get_by_asset(ca['id'])
            cat_total_val_inr += PortfolioService.current_value_inr(ca, ca_txs, rate)
    else:
        cat_total_val_inr = val_inr

    total_networth_inr = 0.0
    for a in all_assets:
        a_cat = CategoryRepository.get_by_id(a['category_id']) if a.get('category_id') else None
        a_rate = PortfolioService.current_inr_exchange_rate(a_cat, currencies) if a_cat else 1.0
        a_txs = TransactionRepository.get_by_asset(a['id'])
        total_networth_inr += PortfolioService.current_value_inr(a, a_txs, a_rate)

    category_allocation_pct = (val_inr / cat_total_val_inr * 100.0) if cat_total_val_inr > 0 else 0.0
    networth_allocation_pct = (val_inr / total_networth_inr * 100.0) if total_networth_inr > 0 else 0.0

    # Recency & Trading Activity
    tx_counts = PortfolioService.transaction_counts(txs, holding_type)
    inception_info = PortfolioService.inception_date_info(txs)
    last_invested_info = PortfolioService.last_invested_date_info(txs)
    recency_status = PortfolioService.recency_status(txs)
    interest_accrued = PortfolioService.total_interest_accrued(asset, txs)

    notes = NoteRepository.get_by_asset(asset_id)
    reminders = ReminderRepository.get_by_asset(asset_id)
    brokers = BrokerRepository.get_all()

    tax_result = FifoService.calculate_tax(asset, txs, rate)

    # Attach active FIFO tax lot details to buy transactions
    if tax_result and tax_result.active_lots:
        lots_dict = {}
        for lot in tax_result.active_lots:
            k = (lot.purchase_date, round(lot.original_units, 4), round(lot.buy_price, 4))
            lots_dict.setdefault(k, []).append(lot)

        for tx in txs:
            if tx['type'] == 'BUY':
                k = (tx['date'], round(tx['units'], 4), round(tx['price_per_unit'], 4))
                matching_list = lots_dict.get(k)
                tx['active_lot'] = matching_list.pop(0) if matching_list else None
            else:
                tx['active_lot'] = None
    else:
        for tx in txs:
            tx['active_lot'] = None

    value_analysis = AnalysisRepository.get_stock_value_analysis(asset_id)
    dcf_analysis = AnalysisRepository.get_stock_dcf_analysis(asset_id)

    dcf_results = None
    if dcf_analysis:
        dcf_results = StockAnalysisService.calculate_dcf(
            cmp=dcf_analysis.get('cmp', asset['current_price']),
            starting_fcf=dcf_analysis.get('starting_fcf', 0.0),
            growth_rate=dcf_analysis.get('growth_rate', 0.0),
            discount_rate=dcf_analysis.get('discount_rate', 10.0),
            terminal_growth=dcf_analysis.get('terminal_growth', 3.0),
            shares=dcf_analysis.get('shares', 1.0)
        )

    subcategories = CategoryRepository.get_subcategories(cat['id']) if cat else []

    from app.services.transaction_type_registry import TransactionTypeRegistry
    allowed_transactions = TransactionTypeRegistry.get_allowed_transactions(holding_type)

    template_name = 'assets/detail_market.html' if holding_type == 'investment' else 'assets/detail_contract.html'

    return render_template(
        template_name,
        asset=asset,
        category=cat,
        categories=all_categories,
        subcategories=subcategories,
        allowed_transactions=allowed_transactions,
        transactions=txs,
        units=units,
        inv_local=inv_local,
        val_local=val_local,
        inv_inr=inv_inr,
        val_inr=val_inr,
        gain_inr=val_inr - inv_inr,
        gain_pct=((val_inr - inv_inr) / inv_inr * 100.0) if inv_inr > 0 else 0.0,
        xirr_val=xirr_val,
        xirr_mode=xirr_mode,
        lifetime_inv_local=lifetime_inv_local,
        lifetime_inv_inr=lifetime_inv_inr,
        lifetime_ret_local=lifetime_ret_local,
        lifetime_ret_inr=lifetime_ret_inr,
        lifetime_div_local=lifetime_div_local,
        lifetime_div_inr=lifetime_div_inr,
        realized_pnl_inr=realized_pnl_inr,
        total_gain_loss_inr=total_gain_loss_inr,
        overall_gain_loss_pct=overall_gain_loss_pct,
        category_allocation_pct=category_allocation_pct,
        networth_allocation_pct=networth_allocation_pct,
        tx_counts=tx_counts,
        inception_info=inception_info,
        last_invested_info=last_invested_info,
        recency_status=recency_status,
        interest_accrued=interest_accrued,
        notes=notes,
        reminders=reminders,
        brokers=brokers,
        tax_result=tax_result,
        value_analysis=value_analysis,
        dcf_analysis=dcf_analysis,
        dcf_results=dcf_results,
        exchange_rate=rate,
        is_sold_off=PortfolioService.is_sold_off(asset, txs)
    )

@assets_bp.route('/assets/add', methods=['POST'])
def add_asset():
    data = {
        'name': request.form.get('name', '').strip(),
        'current_price': float(request.form.get('current_price', 0.0) or 0.0),
        'category_id': int(request.form.get('category_id')),
        'subcategory_id': int(request.form.get('subcategory_id')) if request.form.get('subcategory_id') else None,
        'tax_country': request.form.get('tax_country', 'India'),
        'tax_asset_type': request.form.get('tax_asset_type', 'equity'),
        'holding_type': request.form.get('holding_type', 'investment'),
        'ticker': request.form.get('ticker', '').strip(),
        'aliases_raw': request.form.get('aliases_raw', '').strip(),
        'interest_rate': float(request.form.get('interest_rate', 0.0) or 0.0),
        'principal_amount': float(request.form.get('principal_amount', 0.0) or 0.0),
        'maturity_date': parse_iso_date(request.form.get('maturity_date')) if request.form.get('maturity_date') else None,
        'payout_frequency': request.form.get('payout_frequency', 'cumulative'),
        'premium_amount': float(request.form.get('premium_amount', 0.0) or 0.0),
        'policy_number': request.form.get('policy_number', '').strip(),
        'institution_name': request.form.get('institution_name', '').strip()
    }
    new_id = AssetRepository.create(data)
    flash(f"Asset '{data['name']}' created successfully.", "success")
    return redirect(url_for('assets.asset_detail', asset_id=new_id))

@assets_bp.route('/assets/edit/<int:asset_id>', methods=['POST'])
def edit_asset(asset_id: int):
    existing = AssetRepository.get_by_id(asset_id)
    if not existing:
        flash("Asset not found.", "danger")
        return redirect(url_for('assets.list_assets'))

    name = request.form.get('name', '').strip() or existing['name']
    
    current_price_raw = request.form.get('current_price')
    current_price = float(current_price_raw) if current_price_raw is not None and current_price_raw != '' else existing.get('current_price', 0.0)

    category_id_raw = request.form.get('category_id')
    category_id = int(category_id_raw) if category_id_raw is not None and category_id_raw != '' else existing.get('category_id')

    subcategory_id_raw = request.form.get('subcategory_id')
    subcategory_id = int(subcategory_id_raw) if subcategory_id_raw is not None and subcategory_id_raw != '' else existing.get('subcategory_id')

    tax_country = request.form.get('tax_country', '').strip() or existing.get('tax_country', 'India')
    tax_asset_type = request.form.get('tax_asset_type', '').strip() or existing.get('tax_asset_type', 'equity')
    holding_type = request.form.get('holding_type', '').strip() or existing.get('holding_type', 'investment')
    ticker = request.form.get('ticker', '').strip() if 'ticker' in request.form else existing.get('ticker', '')
    aliases_raw = request.form.get('aliases_raw', '').strip() if 'aliases_raw' in request.form else existing.get('aliases_raw', '')
    is_completed = bool(request.form.get('is_completed')) if 'is_completed' in request.form else existing.get('is_completed', False)

    interest_rate_raw = request.form.get('interest_rate')
    interest_rate = float(interest_rate_raw) if interest_rate_raw is not None and interest_rate_raw != '' else existing.get('interest_rate', 0.0)

    principal_amount_raw = request.form.get('principal_amount')
    principal_amount = float(principal_amount_raw) if principal_amount_raw is not None and principal_amount_raw != '' else existing.get('principal_amount', 0.0)

    maturity_date = parse_iso_date(request.form.get('maturity_date')) if request.form.get('maturity_date') else existing.get('maturity_date')
    payout_frequency = request.form.get('payout_frequency', '').strip() or existing.get('payout_frequency', 'cumulative')

    premium_amount_raw = request.form.get('premium_amount')
    premium_amount = float(premium_amount_raw) if premium_amount_raw is not None and premium_amount_raw != '' else existing.get('premium_amount', 0.0)

    policy_number = request.form.get('policy_number', '').strip() if 'policy_number' in request.form else existing.get('policy_number', '')
    institution_name = request.form.get('institution_name', '').strip() if 'institution_name' in request.form else existing.get('institution_name', '')

    data = {
        'name': name,
        'current_price': current_price,
        'category_id': category_id,
        'subcategory_id': subcategory_id,
        'tax_country': tax_country,
        'tax_asset_type': tax_asset_type,
        'holding_type': holding_type,
        'ticker': ticker,
        'aliases_raw': aliases_raw,
        'is_completed': is_completed,
        'interest_rate': interest_rate,
        'principal_amount': principal_amount,
        'maturity_date': maturity_date,
        'payout_frequency': payout_frequency,
        'premium_amount': premium_amount,
        'policy_number': policy_number,
        'institution_name': institution_name
    }
    AssetRepository.update(asset_id, data)
    flash("Asset updated successfully.", "success")
    return redirect(url_for('assets.asset_detail', asset_id=asset_id))

@assets_bp.route('/assets/delete/<int:asset_id>', methods=['POST'])
def delete_asset(asset_id: int):
    AssetRepository.delete(asset_id)
    flash("Asset deleted.", "info")
    return redirect(url_for('assets.list_assets'))

@assets_bp.route('/assets/bulk-update', methods=['GET', 'POST'])
def bulk_update():
    if request.method == 'POST':
        all_assets = AssetRepository.get_all()
        updated_count = 0
        updated_cat_ids = set()

        for asset in all_assets:
            price_key = f"price_{asset['id']}"
            if price_key in request.form:
                try:
                    new_price = float(request.form[price_key])
                    if abs(new_price - asset['current_price']) > 0.000001:
                        AssetRepository.update_price(asset['id'], new_price)
                        updated_count += 1
                        if asset.get('category_id'):
                            updated_cat_ids.add(asset['category_id'])
                except ValueError:
                    pass

        # Update category last_updated_date for modified asset categories
        from datetime import datetime
        now = datetime.now()
        for cat_id in updated_cat_ids:
            cat = CategoryRepository.get_by_id(cat_id)
            if cat:
                cat['last_updated_date'] = now
                CategoryRepository.update(cat_id, cat)

        flash(f"Updated current prices for {updated_count} assets.", "success")
        return redirect(url_for('assets.list_assets'))

    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    return render_template('assets/bulk_update.html', assets=all_assets, categories=categories)

@assets_bp.route('/assets/update-balance/<int:asset_id>', methods=['POST'])
def update_balance(asset_id: int):
    asset = AssetRepository.get_by_id(asset_id)
    if not asset:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
            return {'success': False, 'error': 'Asset not found'}, 404
        flash("Asset not found.", "danger")
        return redirect(url_for('assets.list_assets'))

    new_price_raw = request.form.get('current_price') or request.form.get('current_balance')
    if new_price_raw is not None:
        try:
            new_price = float(new_price_raw)
            AssetRepository.update_price(asset_id, new_price)

            # Update category last_updated_date matching iOS app
            if asset.get('category_id'):
                cat = CategoryRepository.get_by_id(asset['category_id'])
                if cat:
                    from datetime import datetime
                    cat['last_updated_date'] = datetime.now()
                    CategoryRepository.update(asset['category_id'], cat)

            msg = f"Updated balance for '{asset['name']}' to {new_price:,.2f}."
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return {'success': True, 'message': msg, 'asset_id': asset_id, 'new_balance': new_price}
            flash(msg, "success")
        except ValueError:
            flash("Invalid amount entered.", "danger")

    redirect_to = request.form.get('redirect_to')
    if redirect_to:
        return redirect(redirect_to)
    return redirect(url_for('assets.asset_detail', asset_id=asset_id))

