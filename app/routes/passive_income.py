from datetime import datetime
from flask import Blueprint, render_template, request
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.broker_repository import BrokerRepository
from app.services.portfolio_service import PortfolioService

passive_income_bp = Blueprint('passive_income', __name__)

def is_passive_income_tx(tx: dict, category: dict = None) -> bool:
    raw = (tx.get('raw_type') or tx.get('type') or '').strip().upper()

    # EXCLUSION LIST: Employer contributions, Employee contributions, Deposits, Withdrawals, Buy, Sell, Premiums, Surrender, Maturity
    excluded_keywords = [
        'EMPLOYER', 'EMPLOYEE', 'CONTRIBUTION', 'BUY', 'SELL',
        'DEPOSIT', 'WITHDRAWAL', 'MATURITY', 'SURRENDER', 'PREMIUM'
    ]
    for kw in excluded_keywords:
        if kw in raw:
            return False

    # Standard yield types
    is_yield = (
        tx.get('type') == 'DIVIDEND' or
        any(k in raw for k in ['DIVIDEND', 'INTEREST', 'BONUS', 'SURVIVAL', 'COUPON', 'RENT', 'ROYALTY'])
    )

    if category and category.get('passive_transaction_types'):
        active_rules = category['passive_transaction_types']
        if active_rules:
            if raw in active_rules or tx.get('type') in active_rules:
                return True
            return any(r in raw for r in active_rules)

    return is_yield

def income_category_group(raw_type: str, tx_type: str) -> str:
    raw = (raw_type or tx_type or '').upper()
    if 'DIVIDEND' in raw or tx_type == 'DIVIDEND':
        return 'dividends'
    elif 'INTEREST' in raw:
        return 'interest'
    elif 'COUPON' in raw or 'BONUS' in raw or 'SURVIVAL' in raw:
        return 'benefits'
    return 'dividends'

@passive_income_bp.route('/passive-income')
def index():
    all_txs = TransactionRepository.get_all()
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()
    brokers = BrokerRepository.get_all()

    current_year = datetime.now().year
    current_month = datetime.now().month

    period_type = request.args.get('period', 'monthly') # monthly, yearly, lifetime
    selected_year = request.args.get('year', type=int) or current_year
    selected_month = request.args.get('month', type=int) or current_month
    income_filter = request.args.get('filter', 'all') # all, dividends, interest, benefits

    cat_map = {c['id']: c for c in categories}
    cat_by_name = {c['name']: c for c in categories}
    asset_map = {a['id']: a for a in all_assets}

    # Filter base passive transactions
    passive_tx_list = []
    years_set = set([current_year])

    for tx in all_txs:
        cat = cat_by_name.get(tx.get('category_name')) or (cat_map.get(tx.get('category_id')) if tx.get('category_id') else None)
        if not is_passive_income_tx(tx, cat):
            continue

        tx_year = tx['date'].year
        tx_month = tx['date'].month
        years_set.add(tx_year)

        # Category group check (dividends, interest, benefits)
        grp = income_category_group(tx.get('raw_type'), tx.get('type'))
        if income_filter != 'all' and grp != income_filter:
            continue

        rate = tx.get('inr_exchange_rate') or (PortfolioService.current_inr_exchange_rate(cat, currencies) if cat else 1.0)
        units = tx.get('units', 0.0)
        price = tx.get('price_per_unit', 0.0)
        raw_amt = (units * price) if (units > 0 and tx.get('type') == 'DIVIDEND') else price
        amt_inr = raw_amt * rate

        passive_tx_list.append({
            'tx': tx,
            'year': tx_year,
            'month': tx_month,
            'group': grp,
            'amount_inr': amt_inr,
            'category': cat,
            'asset': asset_map.get(tx['asset_id'])
        })

    sorted_years = sorted(list(years_set), reverse=True)
    starting_year = min(years_set) if years_set else current_year

    # Filter by period type
    period_txs = []
    for item in passive_tx_list:
        if period_type == 'lifetime':
            period_txs.append(item)
        elif period_type == 'yearly':
            if item['year'] == selected_year:
                period_txs.append(item)
        else: # monthly
            if item['year'] == selected_year and item['month'] == selected_month:
                period_txs.append(item)

    # Compute KPI Metrics
    total_income = sum(item['amount_inr'] for item in period_txs)
    total_count = len(period_txs)
    total_dividends = sum(item['amount_inr'] for item in period_txs if item['group'] == 'dividends')
    total_interest = sum(item['amount_inr'] for item in period_txs if item['group'] == 'interest')
    total_other = sum(item['amount_inr'] for item in period_txs if item['group'] == 'benefits')

    if period_type == 'monthly':
        monthly_avg = total_income
    elif period_type == 'yearly':
        monthly_avg = total_income / 12.0
    else:
        num_months = max(1.0, float(current_year - starting_year + 1) * 12.0)
        monthly_avg = total_income / num_months

    # Top producing asset
    asset_totals = {}
    for item in period_txs:
        a_name = item['tx'].get('asset_name', 'Unknown Asset')
        asset_totals[a_name] = asset_totals.get(a_name, 0.0) + item['amount_inr']

    top_asset = None
    if asset_totals:
        best_name = max(asset_totals, key=asset_totals.get)
        top_asset = {'name': best_name, 'amount_inr': asset_totals[best_name]}

    # Category Flows Breakdown (for Monthly View)
    cat_flows_map = {}
    for item in period_txs:
        c_name = item['tx'].get('category_name', 'Uncategorized')
        if c_name not in cat_flows_map:
            cat_flows_map[c_name] = {
                'category_name': c_name,
                'total_income': 0.0,
                'count': 0,
                'dividends': 0.0,
                'interest': 0.0,
                'other': 0.0,
                'assets': {}
            }
        cat_flows_map[c_name]['total_income'] += item['amount_inr']
        cat_flows_map[c_name]['count'] += 1
        if item['group'] == 'dividends':
            cat_flows_map[c_name]['dividends'] += item['amount_inr']
        elif item['group'] == 'interest':
            cat_flows_map[c_name]['interest'] += item['amount_inr']
        else:
            cat_flows_map[c_name]['other'] += item['amount_inr']

        a_name = item['tx'].get('asset_name', 'Unknown Asset')
        if a_name not in cat_flows_map[c_name]['assets']:
            cat_flows_map[c_name]['assets'][a_name] = {'name': a_name, 'total_income': 0.0, 'count': 0}
        cat_flows_map[c_name]['assets'][a_name]['total_income'] += item['amount_inr']
        cat_flows_map[c_name]['assets'][a_name]['count'] += 1

    category_flows = []
    for c_name, c_data in cat_flows_map.items():
        sorted_asset_flows = sorted(list(c_data['assets'].values()), key=lambda x: x['total_income'], reverse=True)
        category_flows.append({
            'category_name': c_name,
            'total_income': c_data['total_income'],
            'count': c_data['count'],
            'dividends': c_data['dividends'],
            'interest': c_data['interest'],
            'other': c_data['other'],
            'asset_flows': sorted_asset_flows
        })
    category_flows.sort(key=lambda x: x['total_income'], reverse=True)

    # Yearly Matrix Grid Data (Selected Year)
    yearly_matrix = []
    year_tx_all = [item for item in passive_tx_list if item['year'] == selected_year]
    cat_year_groups = {}
    for item in year_tx_all:
        c_name = item['tx'].get('category_name', 'Uncategorized')
        if c_name not in cat_year_groups:
            cat_year_groups[c_name] = {'category_name': c_name, 'monthly': {m: 0.0 for m in range(1, 13)}, 'assets': {}}
        m = item['month']
        cat_year_groups[c_name]['monthly'][m] += item['amount_inr']

        a_name = item['tx'].get('asset_name', 'Unknown Asset')
        if a_name not in cat_year_groups[c_name]['assets']:
            cat_year_groups[c_name]['assets'][a_name] = {'name': a_name, 'monthly': {m: 0.0 for m in range(1, 13)}}
        cat_year_groups[c_name]['assets'][a_name]['monthly'][m] += item['amount_inr']

    for c_name, c_data in cat_year_groups.items():
        c_total = sum(c_data['monthly'].values())
        a_rows = []
        for a_name, a_data in c_data['assets'].items():
            a_total = sum(a_data['monthly'].values())
            a_rows.append({'name': a_name, 'monthly': a_data['monthly'], 'total': a_total})
        a_rows.sort(key=lambda x: x['total'], reverse=True)
        yearly_matrix.append({'category_name': c_name, 'monthly': c_data['monthly'], 'total': c_total, 'assets': a_rows})
    yearly_matrix.sort(key=lambda x: x['total'], reverse=True)

    # Lifetime Matrix Grid Data (All Years)
    lifetime_matrix = []
    lifetime_years = sorted(list(years_set))
    cat_life_groups = {}
    for item in passive_tx_list:
        c_name = item['tx'].get('category_name', 'Uncategorized')
        if c_name not in cat_life_groups:
            cat_life_groups[c_name] = {'category_name': c_name, 'yearly': {y: 0.0 for y in lifetime_years}, 'assets': {}}
        y = item['year']
        cat_life_groups[c_name]['yearly'][y] = cat_life_groups[c_name]['yearly'].get(y, 0.0) + item['amount_inr']

        a_name = item['tx'].get('asset_name', 'Unknown Asset')
        if a_name not in cat_life_groups[c_name]['assets']:
            cat_life_groups[c_name]['assets'][a_name] = {'name': a_name, 'yearly': {y: 0.0 for y in lifetime_years}}
        cat_life_groups[c_name]['assets'][a_name]['yearly'][y] = cat_life_groups[c_name]['assets'][a_name]['yearly'].get(y, 0.0) + item['amount_inr']

    for c_name, c_data in cat_life_groups.items():
        c_total = sum(c_data['yearly'].values())
        a_rows = []
        for a_name, a_data in c_data['assets'].items():
            a_total = sum(a_data['yearly'].values())
            a_rows.append({'name': a_name, 'yearly': a_data['yearly'], 'total': a_total})
        a_rows.sort(key=lambda x: x['total'], reverse=True)
        lifetime_matrix.append({'category_name': c_name, 'yearly': c_data['yearly'], 'total': c_total, 'assets': a_rows})
    lifetime_matrix.sort(key=lambda x: x['total'], reverse=True)

    return render_template(
        'passive_income.html',
        categories=categories,
        all_assets=all_assets,
        brokers=brokers,
        period_type=period_type,
        selected_year=selected_year,
        selected_month=selected_month,
        income_filter=income_filter,
        available_years=sorted_years,
        starting_year=starting_year,
        current_year=current_year,
        total_income=total_income,
        total_count=total_count,
        total_dividends=total_dividends,
        total_interest=total_interest,
        total_other=total_other,
        monthly_avg=monthly_avg,
        top_asset=top_asset,
        category_flows=category_flows,
        yearly_matrix=yearly_matrix,
        lifetime_matrix=lifetime_matrix,
        lifetime_years=lifetime_years,
        period_txs=period_txs
    )
