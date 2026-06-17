from flask import render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta, date
from . import inventory
from ..models import db, InventoryItem, ShoppingItem, StockChange
from ..constants import CATEGORIES, PURPOSES

# Hilfsfunktion: gibt nur Artikel des eigenen Haushalts zurück
def household_items_query():
    return InventoryItem.query.filter_by(household_id=current_user.household_id)

# Dashboard / Startseite mit Übersicht
@inventory.route('/')
@inventory.route('/dashboard')
@login_required
def dashboard():
    today = date.today()
    soon_date = today + timedelta(days=3)   # "bald" = innerhalb von 3 Tagen

    items = household_items_query().all()

    total_items = len(items)
    # Bald ablaufende (oder bereits abgelaufene) Artikel
    expiring = [i for i in items if i.expiry_date and i.expiry_date <= soon_date]
    # Artikel, deren Menge die Mindestmenge erreicht/unterschritten hat
    low_stock = [i for i in items if i.quantity <= i.min_quantity]
    # Anzahl offener Artikel auf der Einkaufsliste
    open_shopping = ShoppingItem.query.filter_by(
        household_id=current_user.household_id, is_bought=False
    ).count()

    return render_template('inventory/dashboard.html',
                           total_items=total_items,
                           expiring=expiring,
                           low_stock=low_stock,
                           open_shopping=open_shopping,
                           today=today)

# Alle Inventar-Artikel anzeigen (mit optionalem Kategorie-Filter)
@inventory.route('/inventory')
@login_required
def list_items():
    today = date.today()
    soon_date = today + timedelta(days=3)

    # Filter aus der URL lesen (z.B. /inventory?category=Lebensmittel)
    selected_category = request.args.get('category', '')
    selected_purpose = request.args.get('purpose', '')

    query = household_items_query()
    if selected_category:
        query = query.filter_by(category=selected_category)
    if selected_purpose:
        query = query.filter_by(purpose=selected_purpose)

    items = query.all()

    return render_template('inventory/list.html',
                           items=items,
                           categories=CATEGORIES,
                           purposes=PURPOSES,
                           selected_category=selected_category,
                           selected_purpose=selected_purpose,
                           today=today,
                           soon_date=soon_date)

# Neuen Artikel hinzufügen
@inventory.route('/inventory/add', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        # Ablaufdatum verarbeiten (kann leer sein)
        expiry = request.form.get('expiry_date')
        expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date() if expiry else None

        new_item = InventoryItem(
            name=request.form.get('name'),
            category=request.form.get('category'),
            location=request.form.get('location'),
            quantity=float(request.form.get('quantity') or 1),
            unit=request.form.get('unit'),
            expiry_date=expiry_date,
            min_quantity=float(request.form.get('min_quantity') or 1),
            description=request.form.get('description'),
            purpose=request.form.get('purpose'),
            household_id=current_user.household_id
        )
        db.session.add(new_item)
        db.session.commit()
        flash('Artikel hinzugefügt.')
        return redirect(url_for('inventory.list_items'))

    return render_template('inventory/add.html',
                           categories=CATEGORIES, purposes=PURPOSES)

# Artikel bearbeiten (Stammdaten, NICHT die Menge – die läuft über "Bestand anpassen")
@inventory.route('/inventory/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)

    # Sicherstellen dass der Artikel zum eigenen Haushalt gehört
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('inventory.list_items'))

    if request.method == 'POST':
        item.name = request.form.get('name')
        item.category = request.form.get('category')
        item.location = request.form.get('location')
        item.unit = request.form.get('unit')
        item.min_quantity = float(request.form.get('min_quantity') or 1)
        item.description = request.form.get('description')
        item.purpose = request.form.get('purpose')
        expiry = request.form.get('expiry_date')
        item.expiry_date = datetime.strptime(expiry, '%Y-%m-%d').date() if expiry else None

        db.session.commit()
        flash('Artikel aktualisiert.')
        return redirect(url_for('inventory.detail', item_id=item.id))

    return render_template('inventory/edit.html', item=item,
                           categories=CATEGORIES, purposes=PURPOSES)

# Artikel-Detailseite (mit Beschreibung + Änderungshistorie)
@inventory.route('/inventory/<int:item_id>')
@login_required
def detail(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('inventory.list_items'))

    # Historie, neueste Änderung zuerst
    changes = StockChange.query.filter_by(item_id=item.id)\
        .order_by(StockChange.timestamp.desc()).all()

    return render_template('inventory/detail.html', item=item, changes=changes)

# GESCHÄFTSLOGIK: Bestand anpassen + in der Historie protokollieren
@inventory.route('/inventory/adjust/<int:item_id>', methods=['POST'])
@login_required
def adjust_stock(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('inventory.list_items'))

    # Wert kann positiv (+) oder negativ (-) sein, z.B. -4 oder 12
    try:
        change_amount = float(request.form.get('change_amount'))
    except (TypeError, ValueError):
        flash('Bitte eine gültige Zahl eingeben.')
        return redirect(url_for('inventory.detail', item_id=item.id))

    if change_amount == 0:
        flash('Keine Änderung (0 eingegeben).')
        return redirect(url_for('inventory.detail', item_id=item.id))

    note = request.form.get('note')
    quantity_before = item.quantity
    quantity_after = quantity_before + change_amount

    # Bestand darf nicht negativ werden
    if quantity_after < 0:
        flash('Bestand kann nicht unter 0 fallen.')
        return redirect(url_for('inventory.detail', item_id=item.id))

    # Menge aktualisieren
    item.quantity = quantity_after

    # Eintrag in der Änderungshistorie anlegen
    change = StockChange(
        item_id=item.id,
        item_name=item.name,
        user_id=current_user.id,
        change_amount=change_amount,
        quantity_before=quantity_before,
        quantity_after=quantity_after,
        note=note
    )
    db.session.add(change)
    db.session.commit()
    flash(f'Bestand angepasst: {quantity_before} → {quantity_after} {item.unit or ""}')
    return redirect(url_for('inventory.detail', item_id=item.id))

# Artikel löschen
@inventory.route('/inventory/delete/<int:item_id>')
@login_required
def delete_item(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('inventory.list_items'))

    db.session.delete(item)
    db.session.commit()
    flash('Artikel gelöscht.')
    return redirect(url_for('inventory.list_items'))

# GESCHÄFTSLOGIK: Artikel auf Einkaufsliste setzen
@inventory.route('/inventory/to-shopping/<int:item_id>')
@login_required
def add_to_shopping(item_id):
    item = InventoryItem.query.get_or_404(item_id)
    if item.household_id != current_user.household_id:
        flash('Kein Zugriff.')
        return redirect(url_for('inventory.list_items'))

    # Prüfen ob Artikel schon auf der Einkaufsliste ist
    existing = ShoppingItem.query.filter_by(
        name=item.name, household_id=current_user.household_id, is_bought=False
    ).first()

    if not existing:
        shopping_item = ShoppingItem(
            name=item.name,
            category=item.category,
            quantity=item.min_quantity,
            unit=item.unit,
            household_id=current_user.household_id
        )
        db.session.add(shopping_item)
        db.session.commit()
        flash(f'"{item.name}" zur Einkaufsliste hinzugefügt.')
    else:
        flash(f'"{item.name}" ist bereits auf der Einkaufsliste.')

    return redirect(url_for('inventory.list_items'))