from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from . import shopping
from ..models import db, ShoppingItem, InventoryItem, StockChange
from ..constants import CATEGORIES

# Einkaufsliste anzeigen
@shopping.route('/shopping')
@login_required
def list_items():
    # Noch zu kaufende und bereits gekaufte Artikel getrennt (pro Haushalt)
    open_items = ShoppingItem.query.filter_by(
        household_id=current_user.household_id, is_bought=False
    ).all()
    bought_items = ShoppingItem.query.filter_by(
        household_id=current_user.household_id, is_bought=True
    ).all()
    return render_template('shopping/list.html',
                           open_items=open_items,
                           bought_items=bought_items)

# Artikel zur Einkaufsliste hinzufügen
@shopping.route('/shopping/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        new_item = ShoppingItem(
            name=request.form.get('name'),
            category=request.form.get('category'),
            quantity=float(request.form.get('quantity') or 1),
            unit=request.form.get('unit'),
            household_id=current_user.household_id
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Artikel zur Einkaufsliste hinzugefügt.')
        return redirect(url_for('shopping.list_items'))

    return render_template('shopping/add.html', categories=CATEGORIES)

# GESCHÄFTSLOGIK: Artikel als gekauft markieren -> wandert ins Inventar (+ Historie)
@shopping.route('/shopping/buy/<int:item_id>')
@login_required
def mark_bought(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('shopping.list_items'))

    item.is_bought = True

    # Artikel ins Inventar übernehmen (im selben Haushalt)
    existing = InventoryItem.query.filter_by(
        name=item.name, household_id=current_user.household_id
    ).first()

    if existing:
        # Wenn schon im Inventar: Menge erhöhen + Historie-Eintrag
        quantity_before = existing.quantity
        existing.quantity += item.quantity
        change = StockChange(
            item_id=existing.id,
            item_name=existing.name,
            user_id=current_user.id,
            change_amount=item.quantity,
            quantity_before=quantity_before,
            quantity_after=existing.quantity,
            note='Einkauf übernommen'
        )
        db.session.add(change)
    else:
        # Sonst neu im Inventar anlegen
        new_inv = InventoryItem(
            name=item.name,
            category=item.category,
            quantity=item.quantity,
            unit=item.unit,
            household_id=current_user.household_id
        )
        db.session.add(new_inv)

    db.session.commit()
    flash(f'"{item.name}" gekauft und ins Inventar übernommen.')
    return redirect(url_for('shopping.list_items'))

# Artikel löschen
@shopping.route('/shopping/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = ShoppingItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('shopping.list_items'))

    db.session.delete(item)
    db.session.commit()
    flash('Artikel gelöscht.')
    return redirect(url_for('shopping.list_items'))