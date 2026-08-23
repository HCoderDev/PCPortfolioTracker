from flask import Blueprint, request, redirect, url_for, flash, jsonify
from app.repositories.transaction_repository import TransactionRepository
from app.utils.date_utils import parse_iso_date

transactions_bp = Blueprint('transactions', __name__)

def is_ajax():
    return (
        request.is_json or
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'application/json' in request.headers.get('Accept', '')
    )

@transactions_bp.route('/transactions/add', methods=['POST'])
def add_transaction():
    if request.is_json:
        req_data = request.get_json()
    else:
        req_data = request.form

    asset_id = int(req_data.get('asset_id'))
    tx_type = req_data.get('type', 'BUY').upper()
    raw_type = req_data.get('raw_type', tx_type).upper()

    is_income = tx_type in ['DIVIDEND', 'INTEREST'] or raw_type in ['DIVIDEND', 'INTEREST', 'INTEREST_PAYOUT', 'BONUS', 'COUPON', 'SURVIVAL_BENEFIT']
    units = 1.0 if is_income else float(req_data.get('units', 0.0) or 0.0)
    price_per_unit = float(req_data.get('price_per_unit', 0.0) or 0.0)
    tx_date = parse_iso_date(req_data.get('date'))
    broker_id = int(req_data.get('broker_id')) if req_data.get('broker_id') else None
    inr_rate = float(req_data.get('inr_exchange_rate')) if req_data.get('inr_exchange_rate') else None
    notes = str(req_data.get('notes', '')).strip()

    data = {
        'asset_id': asset_id,
        'broker_id': broker_id,
        'type': tx_type,
        'raw_type': raw_type,
        'units': units,
        'price_per_unit': price_per_unit,
        'date': tx_date,
        'inr_exchange_rate': inr_rate,
        'notes': notes
    }
    new_id = TransactionRepository.create(data)

    if is_ajax():
        return jsonify({'status': 'success', 'message': 'Transaction recorded.', 'id': new_id, 'asset_id': asset_id})

    flash("Transaction recorded.", "success")
    next_url = request.form.get('next') or url_for('assets.asset_detail', asset_id=asset_id)
    return redirect(next_url)

@transactions_bp.route('/transactions/edit/<int:tx_id>', methods=['POST'])
def edit_transaction(tx_id: int):
    tx = TransactionRepository.get_by_id(tx_id)
    if not tx:
        if is_ajax():
            return jsonify({'status': 'error', 'message': 'Transaction not found.'}), 404
        flash("Transaction not found.", "danger")
        return redirect(url_for('flows.index'))

    if request.is_json:
        req_data = request.get_json()
    else:
        req_data = request.form

    tx_type = req_data.get('type', tx['type']).upper()
    raw_type = req_data.get('raw_type', tx['raw_type']).upper()
    
    is_income = tx_type in ['DIVIDEND', 'INTEREST'] or raw_type in ['DIVIDEND', 'INTEREST', 'INTEREST_PAYOUT', 'BONUS', 'COUPON', 'SURVIVAL_BENEFIT']
    units = 1.0 if is_income else float(req_data.get('units', tx['units']) or 0.0)
    price_per_unit = float(req_data.get('price_per_unit', tx['price_per_unit']) or 0.0)
    tx_date = parse_iso_date(req_data.get('date')) if req_data.get('date') else tx['date']
    broker_id = int(req_data.get('broker_id')) if req_data.get('broker_id') else tx['broker_id']
    inr_rate = float(req_data.get('inr_exchange_rate')) if req_data.get('inr_exchange_rate') else tx['inr_exchange_rate']
    notes = str(req_data.get('notes', tx['notes'])).strip()

    data = {
        'asset_id': tx['asset_id'],
        'broker_id': broker_id,
        'type': tx_type,
        'raw_type': raw_type,
        'units': units,
        'price_per_unit': price_per_unit,
        'date': tx_date,
        'inr_exchange_rate': inr_rate,
        'notes': notes
    }
    TransactionRepository.update(tx_id, data)

    if is_ajax():
        return jsonify({'status': 'success', 'message': 'Transaction updated.', 'id': tx_id, 'asset_id': tx['asset_id']})

    flash("Transaction updated.", "success")
    return redirect(url_for('assets.asset_detail', asset_id=tx['asset_id']))

@transactions_bp.route('/transactions/delete/<int:tx_id>', methods=['POST'])
def delete_transaction(tx_id: int):
    tx = TransactionRepository.get_by_id(tx_id)
    asset_id = tx['asset_id'] if tx else None
    TransactionRepository.delete(tx_id)

    if is_ajax():
        return jsonify({'status': 'success', 'message': 'Transaction deleted.', 'asset_id': asset_id})

    flash("Transaction deleted.", "info")
    if asset_id:
        return redirect(url_for('assets.asset_detail', asset_id=asset_id))
    return redirect(url_for('flows.index'))
