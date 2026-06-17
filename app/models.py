from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import secrets

db = SQLAlchemy()

# Tabelle: Haushalt (Familie) – alle Mitglieder teilen sich EIN Inventar
class Household(db.Model):
    __tablename__ = 'households'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    invite_code = db.Column(db.String(8), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Beziehungen: ein Haushalt hat viele Mitglieder, Artikel etc.
    members = db.relationship('User', backref='household', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='household', lazy=True)
    shopping_items = db.relationship('ShoppingItem', backref='household', lazy=True)

    @staticmethod
    def generate_invite_code():
        # Erzeugt einen eindeutigen 8-stelligen Einladungscode (z.B. 'A1B2C3D4')
        while True:
            code = secrets.token_hex(4).upper()
            if not Household.query.filter_by(invite_code=code).first():
                return code


# Tabelle: Benutzer (Familienmitglied)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # Jeder Benutzer gehört zu genau einem Haushalt
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)

    # Alle Änderungen, die dieser Benutzer gemacht hat
    stock_changes = db.relationship('StockChange', backref='user', lazy=True)


# Tabelle: Inventar (gehört zum HAUSHALT, nicht mehr zum einzelnen User)
class InventoryItem(db.Model):
    __tablename__ = 'inventory'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    location = db.Column(db.String(50))  # z.B. Kühlschrank, Keller
    quantity = db.Column(db.Float, nullable=False, default=1)
    unit = db.Column(db.String(20))  # z.B. kg, Stück, Liter
    expiry_date = db.Column(db.Date, nullable=True)
    min_quantity = db.Column(db.Float, default=1)  # Mindestmenge
    description = db.Column(db.Text)      # Freitext-Beschreibung des Artikels
    purpose = db.Column(db.String(30))    # Verwendungszweck: verwenden/verkaufen/ersatzteil/lager
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)

    # Historie aller Bestandsänderungen dieses Artikels
    # cascade: wird der Artikel gelöscht, verschwindet auch seine Historie
    changes = db.relationship('StockChange', backref='item', lazy=True,
                              cascade='all, delete-orphan')


# Tabelle: Einkaufsliste (gehört ebenfalls zum Haushalt)
class ShoppingItem(db.Model):
    __tablename__ = 'shopping_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Float, default=1)
    unit = db.Column(db.String(20))
    is_bought = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    household_id = db.Column(db.Integer, db.ForeignKey('households.id'), nullable=False)


# Tabelle: ÄNDERUNGSHISTORIE – wer hat wann wie viel geändert
class StockChange(db.Model):
    __tablename__ = 'stock_changes'
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('inventory.id'), nullable=False)
    item_name = db.Column(db.String(100))   # Name zum Zeitpunkt der Änderung
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    change_amount = db.Column(db.Float, nullable=False)   # z.B. -4 oder +12
    quantity_before = db.Column(db.Float)
    quantity_after = db.Column(db.Float)
    note = db.Column(db.String(200))   # optionale Notiz, z.B. "Abendessen"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)