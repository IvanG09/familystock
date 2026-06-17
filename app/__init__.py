from flask import Flask
from flask_login import LoginManager
from flask_jwt_extended import JWTManager
from flask_wtf.csrf import CSRFProtect
from .models import db, User
from config import Config

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Datenbank initialisieren
    db.init_app(app)

    # Login Manager initialisieren
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Bitte melde dich an.'

    # JWT für API initialisieren
    jwt = JWTManager(app)
    
    # CSRF-Schutz aktivieren (schützt die Web-Formulare)
    csrf.init_app(app)

    # Das API nutzt Token-Auth (JWT), kein Browser-Formular -> CSRF dort ausnehmen
    from .api import api as api_bp_for_csrf
    csrf.exempt(api_bp_for_csrf)

    # User laden (wird von Flask-Login benötigt)
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprints registrieren (die verschiedenen Bereiche der App)
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .inventory import inventory as inventory_blueprint
    app.register_blueprint(inventory_blueprint)

    from .shopping import shopping as shopping_blueprint
    app.register_blueprint(shopping_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    # Datenbank-Tabellen erstellen
    with app.app_context():
        db.create_all()

    return app