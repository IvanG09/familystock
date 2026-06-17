from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash
from . import api
from ..models import db, User, InventoryItem, ShoppingItem, StockChange

# Hilfsfunktion: aktuellen User aus dem Token holen
def current_api_user():
    user_id = get_jwt_identity()
    return User.query.get(int(user_id))

# API-LOGIN: Token anfordern (ohne Browser, z.B. mit curl/Postman)
@api.route('/login', methods=['POST'])
def api_login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Keine Daten gesendet'}), 400

    username = data.get('username')
    password = data.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password, password):
        # Token erstellen (gültig für API-Zugriff)
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token}), 200

    return jsonify({'error': 'Falscher Benutzername oder Passwort'}), 401

# INVENTAR abrufen (lesender Zugriff, geschützt mit Token)
@api.route('/inventory', methods=['GET'])
@jwt_required()
def get_inventory():
    user = current_api_user()
    items = InventoryItem.query.filter_by(household_id=user.household_id).all()

    result = []
    for item in items:
        result.append({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'location': item.location,
            'quantity': item.quantity,
            'unit': item.unit,
            'purpose': item.purpose,
            'description': item.description,
            'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
            'min_quantity': item.min_quantity
        })

    return jsonify(result), 200

# EINKAUFSLISTE abrufen (lesender Zugriff, geschützt mit Token)
@api.route('/shopping', methods=['GET'])
@jwt_required()
def get_shopping():
    user = current_api_user()
    items = ShoppingItem.query.filter_by(
        household_id=user.household_id, is_bought=False
    ).all()

    result = []
    for item in items:
        result.append({
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'quantity': item.quantity,
            'unit': item.unit
        })

    return jsonify(result), 200

# Einzelnen Inventar-Artikel abrufen
@api.route('/inventory/<int:item_id>', methods=['GET'])
@jwt_required()
def get_inventory_item(item_id):
    user = current_api_user()
    item = InventoryItem.query.filter_by(
        id=item_id, household_id=user.household_id
    ).first()

    if not item:
        return jsonify({'error': 'Artikel nicht gefunden'}), 404

    return jsonify({
        'id': item.id,
        'name': item.name,
        'category': item.category,
        'location': item.location,
        'quantity': item.quantity,
        'unit': item.unit,
        'purpose': item.purpose,
        'description': item.description,
        'expiry_date': item.expiry_date.isoformat() if item.expiry_date else None,
        'min_quantity': item.min_quantity
    }), 200

# ÄNDERUNGSHISTORIE eines Artikels abrufen (lesender Zugriff)
@api.route('/inventory/<int:item_id>/history', methods=['GET'])
@jwt_required()
def get_item_history(item_id):
    user = current_api_user()
    item = InventoryItem.query.filter_by(
        id=item_id, household_id=user.household_id
    ).first()

    if not item:
        return jsonify({'error': 'Artikel nicht gefunden'}), 404

    changes = StockChange.query.filter_by(item_id=item.id)\
        .order_by(StockChange.timestamp.desc()).all()

    result = []
    for change in changes:
        result.append({
            'timestamp': change.timestamp.isoformat(),
            'user': change.user.username,   # WER hat die Änderung gemacht
            'change_amount': change.change_amount,
            'quantity_before': change.quantity_before,
            'quantity_after': change.quantity_after,
            'note': change.note
        })

    return jsonify({
        'item': item.name,
        'history': result
    }), 200