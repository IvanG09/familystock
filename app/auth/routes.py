from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from . import auth
from ..models import db, User, Household

# Registrierung neuer Benutzer
@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        # Der Benutzer wählt: neuen Haushalt erstellen ODER beitreten
        mode = request.form.get('mode')  # 'create' oder 'join'

        # Passwort-Mindestanforderung: mindestens 8 Zeichen
        if not password or len(password) < 8:
            flash('Das Passwort muss mindestens 8 Zeichen lang sein.')
            return redirect(url_for('auth.register'))

        # Prüfen ob Benutzername oder E-Mail schon existiert
        if User.query.filter_by(username=username).first():
            flash('Benutzername ist bereits vergeben.')
            return redirect(url_for('auth.register'))
        if User.query.filter_by(email=email).first():
            flash('E-Mail ist bereits registriert.')
            return redirect(url_for('auth.register'))

        # Haushalt bestimmen
        if mode == 'join':
            # Bestehendem Haushalt per Einladungscode beitreten
            invite_code = request.form.get('invite_code', '').strip().upper()
            household = Household.query.filter_by(invite_code=invite_code).first()
            if not household:
                flash('Ungültiger Einladungscode.')
                return redirect(url_for('auth.register'))
        else:
            # Neuen Haushalt erstellen
            household_name = request.form.get('household_name', '').strip()
            if not household_name:
                flash('Bitte einen Namen für den Haushalt angeben.')
                return redirect(url_for('auth.register'))
            household = Household(
                name=household_name,
                invite_code=Household.generate_invite_code()
            )
            db.session.add(household)
            db.session.flush()  # damit household.id verfügbar ist

        # Neuen Benutzer anlegen (Passwort wird verschlüsselt gespeichert)
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            household_id=household.id
        )
        db.session.add(new_user)
        db.session.commit()

        if mode == 'create':
            flash(f'Haushalt erstellt! Dein Einladungscode lautet: {household.invite_code}')
        else:
            flash('Registrierung erfolgreich! Du kannst dich jetzt anmelden.')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

# Anmeldung
@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        # Prüfen ob Benutzer existiert und Passwort stimmt
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('inventory.list_items'))
        else:
            flash('Falscher Benutzername oder Passwort.')

    return render_template('auth/login.html')

# Abmeldung
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# Haushalt-Info anzeigen (Einladungscode für die Familie)
@auth.route('/household')
@login_required
def household_info():
    from flask_login import current_user
    members = User.query.filter_by(household_id=current_user.household_id).all()
    return render_template('auth/household.html',
                           household=current_user.household,
                           members=members)