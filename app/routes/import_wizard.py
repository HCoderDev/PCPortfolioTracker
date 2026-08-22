from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.asset_repository import AssetRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.category_repository import CategoryRepository
from app.services.import_service import ImportService

import_wizard_bp = Blueprint('import_wizard', __name__)

@import_wizard_bp.route('/import')
def index():
    categories = CategoryRepository.get_all()
    all_assets = AssetRepository.get_all()
    return render_template('import_wizard.html', categories=categories, assets=all_assets)

@import_wizard_bp.route('/import/process', methods=['POST'])
def process_import():
    file = request.files.get('file')
    if not file or not file.filename:
        flash("Please select a valid CSV or XLSX file.", "warning")
        return redirect(url_for('import_wizard.index'))

    content = file.read().decode('utf-8', errors='ignore')
    parsed_rows = ImportService.parse_csv_transactions(content)

    all_assets = AssetRepository.get_all()
    imported_count = 0

    for row in parsed_rows:
        matched_asset = ImportService.match_asset(row['asset_identifier'], all_assets)
        if matched_asset:
            TransactionRepository.create({
                'asset_id': matched_asset['id'],
                'type': row['type'],
                'raw_type': row['type'],
                'units': row['units'],
                'price_per_unit': row['price_per_unit'],
                'date': row['date'],
                'notes': f"Imported: {row['notes']}".strip()
            })
            imported_count += 1

    flash(f"Import process complete! Successfully created {imported_count} transactions.", "success")
    return redirect(url_for('flows.index'))
