from flask import Blueprint, render_template, Response, current_app, send_file, request, flash, redirect, url_for
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.asset_repository import AssetRepository
from app.db import close_db
import csv
import io
import os
import gc

export_bp = Blueprint('export', __name__)

@export_bp.route('/export')
def index():
    db_path = current_app.config.get('DATABASE_PATH', '')
    db_exists = os.path.exists(db_path) if db_path else False
    db_size_mb = round(os.path.getsize(db_path) / (1024 * 1024), 2) if db_exists else 0
    return render_template('export.html', db_path=db_path, db_exists=db_exists, db_size_mb=db_size_mb)

@export_bp.route('/export/csv/<type_str>')
def export_csv(type_str: str):
    output = io.StringIO()
    writer = csv.writer(output)

    if type_str == 'transactions':
        txs = TransactionRepository.get_all()
        writer.writerow(['ID', 'Asset', 'Type', 'Raw Type', 'Units', 'Price Per Unit', 'Date', 'Broker', 'Notes'])
        for t in txs:
            writer.writerow([t['id'], t['asset_name'], t['type'], t['raw_type'], t['units'], t['price_per_unit'], t['date'].strftime('%d-%m-%Y') if t['date'] else '', t['broker_name'], t['notes']])
        filename = "Portfolio_Transactions.csv"
    else:
        assets = AssetRepository.get_all()
        writer.writerow(['ID', 'Name', 'Category', 'Ticker', 'Holding Type', 'Current Price', 'Tax Country', 'Tax Type'])
        for a in assets:
            writer.writerow([a['id'], a['name'], a['category_name'], a['ticker'], a['holding_type'], a['current_price'], a['tax_country'], a['tax_asset_type']])
        filename = "Portfolio_Assets.csv"

    output.seek(0)
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@export_bp.route('/export/db/download')
def download_db():
    db_path = current_app.config.get('DATABASE_PATH')
    if not db_path or not os.path.exists(db_path):
        flash("Database file does not exist to export.", "danger")
        return redirect(url_for('export.index'))
    
    filename = os.path.basename(db_path) or "PortfolioTrackerBackup.db"
    return send_file(db_path, as_attachment=True, download_name=filename)

@export_bp.route('/export/db/import', methods=['POST'])
def import_db():
    if 'db_file' not in request.files:
        flash("No database file provided.", "danger")
        return redirect(url_for('export.index'))
    
    file = request.files['db_file']
    if not file or file.filename == '':
        flash("No file selected for import.", "danger")
        return redirect(url_for('export.index'))
    
    file_bytes = file.read()
    
    # Check standard SQLite 3 header signature
    if not file_bytes.startswith(b'SQLite format 3\x00'):
        flash("Invalid file format. The uploaded file is not a valid SQLite 3 database file.", "danger")
        return redirect(url_for('export.index'))
    
    db_path = current_app.config.get('DATABASE_PATH')
    if not db_path:
        flash("Database path is not configured.", "danger")
        return redirect(url_for('export.index'))

    try:
        # Close current request context DB connection
        close_db()
        gc.collect()

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Blindly replace database file contents
        with open(db_path, 'wb') as f:
            f.write(file_bytes)
        
        flash("Database content blindly replaced and imported successfully! All application views updated.", "success")
    except Exception as e:
        flash(f"Failed to import database: {str(e)}", "danger")

    return redirect(url_for('export.index'))

