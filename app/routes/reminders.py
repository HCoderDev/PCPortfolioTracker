from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.asset_repository import AssetRepository
from app.utils.date_utils import parse_iso_date

reminders_bp = Blueprint('reminders', __name__)

@reminders_bp.route('/reminders')
def index():
    reminders = ReminderRepository.get_all()
    all_assets = AssetRepository.get_all()
    status_filter = request.args.get('status', 'pending')

    if status_filter == 'pending':
        filtered = [r for r in reminders if not r['is_completed']]
    elif status_filter == 'completed':
        filtered = [r for r in reminders if r['is_completed']]
    else:
        filtered = reminders

    return render_template(
        'reminders.html',
        reminders=filtered,
        all_assets=all_assets,
        status_filter=status_filter
    )

@reminders_bp.route('/reminders/add', methods=['POST'])
def add_reminder():
    data = {
        'asset_id': int(request.form.get('asset_id')) if request.form.get('asset_id') else None,
        'title': request.form.get('title', '').strip(),
        'notes': request.form.get('notes', '').strip(),
        'event_date': parse_iso_date(request.form.get('event_date')),
        'is_completed': False
    }
    ReminderRepository.create(data)
    flash("Reminder created.", "success")
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/reminders/toggle/<int:reminder_id>', methods=['POST'])
def toggle_reminder(reminder_id: int):
    is_completed = bool(request.form.get('is_completed'))
    ReminderRepository.toggle_complete(reminder_id, is_completed)
    flash("Reminder status updated.", "info")
    return redirect(url_for('reminders.index'))

@reminders_bp.route('/reminders/delete/<int:reminder_id>', methods=['POST'])
def delete_reminder(reminder_id: int):
    ReminderRepository.delete(reminder_id)
    flash("Reminder deleted.", "info")
    return redirect(url_for('reminders.index'))
