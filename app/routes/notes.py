from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.repositories.note_repository import NoteRepository
from app.repositories.asset_repository import AssetRepository
from app.utils.date_utils import parse_iso_date

notes_bp = Blueprint('notes', __name__)

@notes_bp.route('/notes')
def index():
    notes = NoteRepository.get_all()
    all_assets = AssetRepository.get_all()
    return render_template('notes.html', notes=notes, assets=all_assets)

@notes_bp.route('/notes/add', methods=['POST'])
def add_note():
    data = {
        'asset_id': int(request.form.get('asset_id')) if request.form.get('asset_id') else None,
        'title': request.form.get('title', '').strip(),
        'description': request.form.get('description', '').strip(),
        'date': parse_iso_date(request.form.get('date'))
    }
    NoteRepository.create(data)
    flash("Note saved.", "success")
    next_url = request.form.get('next') or url_for('notes.index')
    return redirect(next_url)

@notes_bp.route('/notes/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id: int):
    NoteRepository.delete(note_id)
    flash("Note deleted.", "info")
    return redirect(url_for('notes.index'))
