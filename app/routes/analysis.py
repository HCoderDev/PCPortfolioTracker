from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.asset_repository import AssetRepository
from app.repositories.analysis_repository import AnalysisRepository
from app.services.stock_analysis_service import StockAnalysisService

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/analysis/value/<int:asset_id>', methods=['GET', 'POST'])
def stock_value_analysis(asset_id: int):
    asset = AssetRepository.get_by_id(asset_id)
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for('assets.list_assets'))

    if request.method == 'POST':
        data = {
            'cmp': float(request.form.get('cmp', asset['current_price']) or 0.0),
            'intrinsic_pe': float(request.form.get('intrinsic_pe', 0.0) or 0.0),
            'industry_pe': float(request.form.get('industry_pe', 0.0) or 0.0),
            'book_value': float(request.form.get('book_value', 0.0) or 0.0),
            'debt_to_equity': float(request.form.get('debt_to_equity', 0.0) or 0.0),
            'free_cash_flow': float(request.form.get('free_cash_flow', 0.0) or 0.0),
            'fcf_ratio': float(request.form.get('fcf_ratio', 0.0) or 0.0),
            'consensus_growth_rate': float(request.form.get('consensus_growth_rate', 0.0) or 0.0),
            'consensus_div_payout_ratio': float(request.form.get('consensus_div_payout_ratio', 0.0) or 0.0),
            'eps_values_string': request.form.get('eps_values_string', '').strip(),
            'dps_values_string': request.form.get('dps_values_string', '').strip(),
            'industry': request.form.get('industry', '').strip(),
            'best_case_pe': float(request.form.get('best_case_pe', 0.0) or 0.0)
        }
        AnalysisRepository.create_or_update_value_analysis(asset_id, data)
        flash("Graham Value Analysis saved.", "success")
        return redirect(url_for('assets.asset_detail', asset_id=asset_id))

    analysis = AnalysisRepository.get_stock_value_analysis(asset_id)
    return render_template('analysis/value.html', asset=asset, analysis=analysis)

@analysis_bp.route('/analysis/dcf/<int:asset_id>', methods=['GET', 'POST'])
def stock_dcf_analysis(asset_id: int):
    asset = AssetRepository.get_by_id(asset_id)
    if not asset:
        flash("Asset not found.", "danger")
        return redirect(url_for('assets.list_assets'))

    if request.method == 'POST':
        data = {
            'cmp': float(request.form.get('cmp', asset['current_price']) or 0.0),
            'starting_fcf': float(request.form.get('starting_fcf', 0.0) or 0.0),
            'growth_rate': float(request.form.get('growth_rate', 0.0) or 0.0),
            'discount_rate': float(request.form.get('discount_rate', 10.0) or 10.0),
            'terminal_growth': float(request.form.get('terminal_growth', 3.0) or 3.0),
            'shares': float(request.form.get('shares', 1.0) or 1.0)
        }
        AnalysisRepository.create_or_update_dcf_analysis(asset_id, data)
        flash("DCF Valuation Model saved.", "success")
        return redirect(url_for('assets.asset_detail', asset_id=asset_id))

    analysis = AnalysisRepository.get_stock_dcf_analysis(asset_id)
    return render_template('analysis/dcf.html', asset=asset, analysis=analysis)

@analysis_bp.route('/analysis/split/<int:asset_id>', methods=['POST'])
def stock_split(asset_id: int):
    split_new = float(request.form.get('split_ratio_new', 1.0))
    split_old = float(request.form.get('split_ratio_old', 1.0))
    StockAnalysisService.process_stock_split(asset_id, split_new, split_old)
    flash(f"Applied Stock Split {int(split_new)}:{int(split_old)}.", "success")
    return redirect(url_for('assets.asset_detail', asset_id=asset_id))
