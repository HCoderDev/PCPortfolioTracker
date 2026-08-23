from flask import Blueprint, render_template, request
from app.repositories.asset_repository import AssetRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.services.portfolio_service import PortfolioService
from app.services.fi_service import FiService
from app.utils.date_utils import parse_iso_date

fi_tracker_bp = Blueprint('fi_tracker', __name__)

@fi_tracker_bp.route('/fi-tracker', methods=['GET', 'POST'])
def index():
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    currencies = CurrencyRepository.get_all()
    user = UserRepository.get_user()

    total_networth_inr = 0.0
    for cat in categories:
        cat_assets = [a for a in all_assets if a['category_id'] == cat['id']]
        rate = PortfolioService.current_inr_exchange_rate(cat, currencies)
        for asset in cat_assets:
            txs = TransactionRepository.get_by_asset(asset['id'])
            total_networth_inr += PortfolioService.current_value_inr(asset, txs, rate)

    target_goal = float(request.form.get('target_goal') or request.args.get('target_goal') or (user.get('target_goal') if user else FiService.DEFAULT_TARGET_GOAL))
    monthly_sip = float(request.form.get('monthly_sip') or request.args.get('monthly_sip') or (user.get('monthly_sip') if user else FiService.DEFAULT_MONTHLY_SIP))
    return_rate = float(request.form.get('return_rate') or request.args.get('return_rate') or (user.get('return_rate') if user else FiService.DEFAULT_RETURN_RATE))
    inflation_rate = float(request.form.get('inflation_rate') or request.args.get('inflation_rate') or (user.get('inflation_rate') if user else FiService.DEFAULT_INFLATION_RATE))
    swr = float(request.form.get('swr') or request.args.get('swr') or (user.get('swr') if user else FiService.DEFAULT_SWR))
    raw_birth_date_str = request.form.get('birth_date') or request.args.get('birth_date') or (user.get('birth_date') if user else "1996-01-01")
    birth_date = parse_iso_date(raw_birth_date_str) if raw_birth_date_str else parse_iso_date("1996-01-01")
    birth_date_iso = birth_date.strftime("%Y-%m-%d")

    if request.method == 'POST' or any(k in request.args for k in ['target_goal', 'monthly_sip', 'return_rate', 'inflation_rate', 'swr', 'birth_date']):
        UserRepository.update_fi_details(
            target_goal=target_goal,
            monthly_sip=monthly_sip,
            return_rate=return_rate,
            inflation_rate=inflation_rate,
            swr=swr,
            birth_date=birth_date_iso
        )

    fi_result = FiService.project_fi(
        current_net_worth=total_networth_inr,
        target_goal=target_goal,
        birth_date=birth_date,
        monthly_sip=monthly_sip,
        return_rate=return_rate,
        inflation_rate=inflation_rate,
        safe_withdrawal_rate=swr
    )

    return render_template(
        'fi_tracker.html',
        fi_result=fi_result,
        target_goal=target_goal,
        monthly_sip=monthly_sip,
        return_rate=return_rate,
        inflation_rate=inflation_rate,
        swr=swr,
        birth_date=birth_date
    )
