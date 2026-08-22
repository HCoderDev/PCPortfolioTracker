from flask import Blueprint, render_template, request, url_for
from app.repositories.category_repository import CategoryRepository
from app.repositories.asset_repository import AssetRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.reminder_repository import ReminderRepository
from app.services.portfolio_service import PortfolioService
from app.services.fi_service import FiService
from app.services.xirr_service import XirrService
from datetime import datetime, timezone

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@dashboard_bp.route('/dashboard')
def index():
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()

    display_currency = request.args.get('currency', 'INR')

    total_networth_inr = 0.0
    total_invested_inr = 0.0
    category_allocations = []
    category_cards = []
    all_portfolio_cfs = []
    underperforming_count = 0
    cash_val_inr = 0.0

    for cat in categories:
        cat_assets = [a for a in all_assets if a['category_id'] == cat['id']]
        cat_invested = 0.0
        cat_current_val = 0.0
        cat_val_inr = 0.0
        cat_inv_inr = 0.0
        asset_rows = []

        inr_rate = PortfolioService.current_inr_exchange_rate(cat, currencies)
        is_cash_cat = 'cash' in cat['name'].lower() or 'bank' in cat['name'].lower()

        for asset in cat_assets:
            txs = TransactionRepository.get_by_asset(asset['id'])
            if PortfolioService.is_sold_off(asset, txs):
                continue

            inv_inr = PortfolioService.invested_value_inr(asset, txs, inr_rate)
            val_inr = PortfolioService.current_value_inr(asset, txs, inr_rate)

            inv = inv_inr if display_currency == "INR" else PortfolioService.invested_value(asset, txs)
            val = val_inr if display_currency == "INR" else PortfolioService.current_value(asset, txs)

            cat_invested += inv
            cat_current_val += val
            cat_val_inr += val_inr
            cat_inv_inr += inv_inr

            gain_loss = val - inv
            gain_loss_pct = ((val - inv) / inv * 100.0) if inv > 0 else 0.0

            if gain_loss_pct < -10.0:
                underperforming_count += 1

            asset_rows.append({
                'asset': asset,
                'value': val,
                'invested': inv,
                'gain_loss': gain_loss,
                'gain_loss_pct': gain_loss_pct
            })

            # Collect cash flows for XIRR computation
            cfs = PortfolioService.cash_flows_inr(asset, txs, inr_rate)
            all_portfolio_cfs.extend(cfs)

        total_networth_inr += cat_val_inr
        total_invested_inr += cat_inv_inr

        if is_cash_cat:
            cash_val_inr += cat_val_inr

        if cat_val_inr > 0:
            category_allocations.append({
                'label': cat['name'],
                'value': cat_val_inr
            })

        category_cards.append({
            'category': cat,
            'invested': cat_invested,
            'current_value': cat_current_val,
            'cat_val_inr': cat_val_inr,
            'gain_loss': cat_current_val - cat_invested,
            'gain_loss_pct': ((cat_current_val - cat_invested) / cat_invested * 100.0) if cat_invested > 0 else 0.0,
            'assets': asset_rows
        })

    # Portfolio Allocation Percentages
    for card in category_cards:
        card['allocation_pct'] = (card['cat_val_inr'] / total_networth_inr * 100.0) if total_networth_inr > 0 else 0.0

    total_gain_loss_inr = total_networth_inr - total_invested_inr
    total_gain_loss_pct = (total_gain_loss_inr / total_invested_inr * 100.0) if total_invested_inr > 0 else 0.0

    # Calculate overall portfolio XIRR
    portfolio_xirr = XirrService.calculate_xirr(all_portfolio_cfs) if all_portfolio_cfs else None

    # Allocation Drift Detection (> +-5% deviation from target allocation)
    targets_sum = sum(c['target_allocation'] for c in categories)
    drifted_categories = []
    if abs(targets_sum - 100.0) < 0.1 and total_networth_inr > 0:
        for card in category_cards:
            cat = card['category']
            actual_pct = card['allocation_pct']
            target_pct = cat['target_allocation']
            drift = actual_pct - target_pct
            if abs(drift) > 5.0:
                drifted_categories.append({
                    'name': cat['name'],
                    'actual_pct': actual_pct,
                    'target_pct': target_pct,
                    'drift': drift
                })

    # Generate Attention Items
    attention_items = []
    if drifted_categories:
        drift_desc = ", ".join([f"{d['name']} ({d['actual_pct']:.1f}% vs target {d['target_pct']:.1f}%)" for d in drifted_categories])
        attention_items.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'title': 'Allocation Drift Detected',
            'description': f'Asset allocations drifted by > ±5% in: {drift_desc}.',
            'link': url_for('rebalancer.index'),
            'link_text': 'Rebalance Portfolio'
        })

    if underperforming_count > 0:
        attention_items.append({
            'type': 'danger',
            'icon': 'fa-arrow-trend-down',
            'title': 'Holdings Down > 10%',
            'description': f'{underperforming_count} active holding{"s are" if underperforming_count > 1 else " is"} currently down more than 10% from cost basis.',
            'link': url_for('assets.list_assets'),
            'link_text': 'View Assets'
        })

    # Check for pending reminders
    reminders = ReminderRepository.get_all()
    pending_reminders = [r for r in reminders if not r['is_completed']]
    if pending_reminders:
        first_rem = pending_reminders[0]
        rem_title = first_rem['title'] or "Upcoming Reminder"
        asset_str = f" for {first_rem['asset_name']}" if first_rem.get('asset_name') else ""
        attention_items.append({
            'type': 'info',
            'icon': 'fa-bell',
            'title': 'Upcoming Reminder',
            'description': f'{rem_title}{asset_str} (Total {len(pending_reminders)} pending)',
            'link': url_for('reminders.index'),
            'link_text': 'View Reminders'
        })

    # High concentration alert
    for card in category_cards:
        if card['allocation_pct'] > 45.0:
            attention_items.append({
                'type': 'info',
                'icon': 'fa-chart-pie',
                'title': 'High Category Concentration',
                'description': f'Portfolio is heavily concentrated in {card["category"]["name"]} ({card["allocation_pct"]:.1f}% of total).',
                'link': url_for('rebalancer.index'),
                'link_text': 'Check Target Allocation'
            })
            break

    # FI Progress Summary
    fi_result = FiService.project_fi(
        current_net_worth=total_networth_inr,
        target_goal=FiService.DEFAULT_TARGET_GOAL,
        birth_date=datetime(1996, 1, 1, tzinfo=timezone.utc),
        monthly_sip=FiService.DEFAULT_MONTHLY_SIP,
        return_rate=FiService.DEFAULT_RETURN_RATE,
        inflation_rate=FiService.DEFAULT_INFLATION_RATE
    )

    return render_template(
        'dashboard.html',
        total_networth_inr=total_networth_inr,
        total_invested_inr=total_invested_inr,
        total_gain_loss_inr=total_gain_loss_inr,
        total_gain_loss_pct=total_gain_loss_pct,
        portfolio_xirr=portfolio_xirr,
        category_allocations=category_allocations,
        category_cards=category_cards,
        drifted_categories=drifted_categories,
        attention_items=attention_items,
        fi_result=fi_result,
        display_currency=display_currency,
        total_categories=len(categories),
        total_assets=len([a for a in all_assets if not PortfolioService.is_sold_off(a, TransactionRepository.get_by_asset(a['id']))])
    )

