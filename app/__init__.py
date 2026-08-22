from flask import Flask
import os
from config import Config
from app.db import close_db
from app.utils.formatters import format_currency, format_percent, format_number, format_inr_commas
from app.utils.date_utils import format_date

import sys

def create_app(config_class=Config):
    if getattr(sys, 'frozen', False):
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        template_folder = os.path.join(base_dir, 'app', 'templates')
        static_folder = os.path.join(base_dir, 'app', 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        app = Flask(__name__)

    app.config.from_object(config_class)

    # Teardown database context
    app.teardown_appcontext(close_db)

    # Register Jinja custom filters
    app.jinja_env.filters['currency'] = format_currency
    app.jinja_env.filters['percent'] = format_percent
    app.jinja_env.filters['number'] = format_number
    app.jinja_env.filters['inr_comma'] = format_inr_commas
    app.jinja_env.filters['date_fmt'] = format_date
    app.jinja_env.filters['abs'] = abs
    app.jinja_env.globals['abs'] = abs

    # Register Blueprints
    from app.routes.dashboard import dashboard_bp
    from app.routes.assets import assets_bp
    from app.routes.categories import categories_bp
    from app.routes.flows import flows_bp
    from app.routes.transactions import transactions_bp
    from app.routes.passive_income import passive_income_bp
    from app.routes.reminders import reminders_bp
    from app.routes.fi_tracker import fi_tracker_bp
    from app.routes.import_wizard import import_wizard_bp
    from app.routes.rebalancer import rebalancer_bp
    from app.routes.tax_planner import tax_planner_bp
    from app.routes.analysis import analysis_bp
    from app.routes.snapshots import snapshots_bp
    from app.routes.settings import settings_bp
    from app.routes.export import export_bp
    from app.routes.notes import notes_bp

    app.register_blueprint(dashboard_bp)
    app.register_blueprint(assets_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(flows_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(passive_income_bp)
    app.register_blueprint(reminders_bp)
    app.register_blueprint(fi_tracker_bp)
    app.register_blueprint(import_wizard_bp)
    app.register_blueprint(rebalancer_bp)
    app.register_blueprint(tax_planner_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(snapshots_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(export_bp)
    app.register_blueprint(notes_bp)

    return app
