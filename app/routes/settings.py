from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.broker_repository import BrokerRepository
from app.repositories.currency_repository import CurrencyRepository
from app.repositories.user_repository import UserRepository

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/brokers')
def list_brokers():
    brokers = BrokerRepository.get_all()
    return render_template('settings/brokers.html', brokers=brokers)

@settings_bp.route('/brokers/add', methods=['POST'])
def add_broker():
    name = request.form.get('name', '').strip()
    if name:
        BrokerRepository.create(name)
        flash(f"Broker '{name}' added.", "success")
    return redirect(url_for('settings.list_brokers'))

@settings_bp.route('/brokers/delete/<int:broker_id>', methods=['POST'])
def delete_broker(broker_id: int):
    BrokerRepository.delete(broker_id)
    flash("Broker deleted.", "info")
    return redirect(url_for('settings.list_brokers'))

@settings_bp.route('/currencies')
def list_currencies():
    currencies = CurrencyRepository.get_all()
    return render_template('settings/currencies.html', currencies=currencies)

@settings_bp.route('/currencies/add', methods=['POST'])
def add_currency():
    code = request.form.get('code', '').strip().upper()
    rate = float(request.form.get('exchange_rate', 1.0) or 1.0)
    is_default = bool(request.form.get('is_default'))
    if code:
        CurrencyRepository.create(code, rate, is_default)
        flash(f"Currency '{code}' added.", "success")
    return redirect(url_for('settings.list_currencies'))

@settings_bp.route('/currencies/update/<int:curr_id>', methods=['POST'])
def update_currency(curr_id: int):
    rate = float(request.form.get('exchange_rate', 1.0) or 1.0)
    is_default = bool(request.form.get('is_default'))
    CurrencyRepository.update(curr_id, rate, is_default)
    flash("Currency exchange rate updated.", "success")
    return redirect(url_for('settings.list_currencies'))

@settings_bp.route('/currencies/bulk-exchange-rates', methods=['GET', 'POST'])
def bulk_exchange_rates():
    from app.repositories.transaction_repository import TransactionRepository
    from app.repositories.asset_repository import AssetRepository
    from app.repositories.category_repository import CategoryRepository

    if request.method == 'POST':
        all_txs = TransactionRepository.get_all()
        foreign_txs = [t for t in all_txs if t.get('currency_code') != 'INR']
        updated_count = 0

        for tx in foreign_txs:
            input_key = f"rate_{tx['id']}"
            if input_key in request.form:
                raw_val = request.form.get(input_key, '').strip()
                if raw_val:
                    try:
                        new_rate = float(raw_val)
                        TransactionRepository.update_exchange_rate(tx['id'], new_rate)
                        updated_count += 1
                    except ValueError:
                        pass
        flash(f"Updated exchange rates for {updated_count} transactions.", "success")
        return redirect(url_for('settings.bulk_exchange_rates'))

    all_txs = TransactionRepository.get_all()
    foreign_txs = [t for t in all_txs if t.get('currency_code') != 'INR']
    categories = CategoryRepository.get_all()
    
    # Group transactions by asset
    grouped = {}
    for tx in foreign_txs:
        asset_name = tx.get('asset_name') or 'Unassigned'
        grouped.setdefault(asset_name, []).append(tx)

    return render_template('settings/bulk_exchange_rates.html', grouped_transactions=grouped, categories=categories)

@settings_bp.route('/settings', methods=['GET', 'POST'])
def user_settings():
    if request.method == 'POST':
        username = request.form.get('username', 'Portfolio User').strip()
        slab_rate = float(request.form.get('tax_slab_rate', 0.30) or 0.30)
        birth_date = request.form.get('birth_date', '').strip() or None
        UserRepository.create_or_update(username, slab_rate, birth_date)
        flash("User settings saved.", "success")
        return redirect(url_for('settings.user_settings'))

    user = UserRepository.get_user()
    return render_template('settings/settings.html', user=user)
