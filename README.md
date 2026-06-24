# 🏠 FamilyStock

**FamilyStock** ist eine Webanwendung zur gemeinsamen Verwaltung von Haushalts­vorräten und Einkaufslisten für die ganze Familie. Mehrere Familienmitglieder teilen sich ein gemeinsames Inventar, sehen wer wann welche Bestände verändert hat und behalten den Überblick über ablaufende Produkte und niedrige Bestände.

Das Projekt entstand im Rahmen der Praxisarbeit *Datenbanken und Webentwicklung (DBWE.TA1A.PA)*.

---

## 📋 Funktionsübersicht

- **Benutzerkonten & Haushalte:** Registrierung mit eindeutigem Benutzernamen und E-Mail. Jeder Benutzer gehört zu einem Haushalt – entweder erstellt er einen neuen oder tritt per Einladungscode einem bestehenden bei.
- **Gemeinsames Inventar:** Alle Mitglieder eines Haushalts verwalten dieselben Artikel (Name, Kategorie, Verwendungszweck, Ort, Menge, Einheit, Mindestmenge, Ablaufdatum, Beschreibung).
- **Bestandshistorie:** Jede Mengenänderung wird protokolliert (wer, wann, vorher → nachher, Notiz).
- **Einkaufsliste:** Gemeinsame Einkaufsliste. Gekaufte Artikel wandern automatisch ins Inventar (mit Historie-Eintrag).
- **Dashboard:** Übersicht mit Kennzahlen, bald ablaufenden Artikeln und Artikeln mit niedrigem Bestand.
- **Filter:** Inventar nach Kategorie und Verwendungszweck filtern.
- **REST-API:** Lesender Zugriff auf Inventar, Einkaufsliste und Historie über ein Token-authentifiziertes API (ohne Browser).

---

## 🛠️ Technologie-Stack

| Komponente | Technologie |
|---|---|
| Programmiersprache | Python 3.9+ |
| Web-Framework | Flask |
| ORM / Datenbankzugriff | Flask-SQLAlchemy |
| Authentifizierung (Web) | Flask-Login |
| Authentifizierung (API) | Flask-JWT-Extended (JWT) |
| CSRF-Schutz | Flask-WTF |
| Datenbank | MySQL / MariaDB (Produktion), SQLite (lokale Entwicklung) |
| MySQL-Treiber | PyMySQL |
| Webserver (Produktion) | Gunicorn |

---

## 📁 Projektstruktur

```
familystock/
├── app/
│   ├── __init__.py          # App-Factory, Erweiterungen, Blueprint-Registrierung
│   ├── models.py            # Datenbankmodelle (Household, User, InventoryItem, ShoppingItem, StockChange)
│   ├── constants.py         # Vordefinierte Kategorien & Verwendungszwecke
│   ├── auth/                # Registrierung, Login, Haushalt
│   ├── inventory/           # Inventar-Verwaltung, Bestand anpassen, Dashboard
│   ├── shopping/            # Einkaufsliste
│   ├── api/                 # RESTful Web-API (JWT)
│   ├── templates/           # HTML-Templates (Jinja2)
│   └── static/css/          # Stylesheet
├── config.py                # Konfiguration (liest aus Umgebungsvariablen)
├── requirements.txt         # Python-Abhängigkeiten
├── Procfile                 # Startbefehl für das Deployment (Gunicorn)
├── run.py                   # Einstiegspunkt
├── .env.example             # Vorlage für Umgebungsvariablen
└── .gitignore
```

---

## 🚀 Lokale Installation

### Voraussetzungen
- Python 3.9 oder höher
- (Optional für Produktion) ein MySQL-/MariaDB-Server

### Schritte

1. **Repository klonen**
   ```bash
   git clone <REPOSITORY-URL>
   cd familystock
   ```

2. **Virtuelle Umgebung erstellen und aktivieren**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS / Linux:
   source venv/bin/activate
   ```

3. **Abhängigkeiten installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **Umgebungsvariablen konfigurieren**

   Kopiere `.env.example` zu `.env` und passe die Werte an:
   ```
   SECRET_KEY=ein-langer-zufaelliger-schluessel
   JWT_SECRET_KEY=ein-weiterer-zufaelliger-schluessel
   DATABASE_URL=sqlite:///familystock.db
   ```
   Für MySQL stattdessen:
   ```
   DATABASE_URL=mysql+pymysql://benutzer:passwort@host:3306/familystock
   ```

5. **Anwendung starten**
   ```bash
   python run.py
   ```
   Die App läuft anschliessend unter `http://127.0.0.1:5000`. Die Datenbanktabellen werden beim ersten Start automatisch erstellt.

---

## 🌐 REST-API

Das API erlaubt lesenden Zugriff auf die Daten eines Haushalts. Die Authentifizierung erfolgt über ein JWT (JSON Web Token), das beim Login angefordert wird – komplett ohne Browser.

### Authentifizierung

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `POST` | `/api/login` | Token anfordern. Body (JSON): `{"username": "...", "password": "..."}` → Antwort: `{"access_token": "..."}` |

Bei allen geschützten Endpunkten muss das Token im Header mitgesendet werden:
```
Authorization: Bearer <access_token>
```

### Endpunkte

| Methode | Endpunkt | Beschreibung |
|---|---|---|
| `GET` | `/api/inventory` | Komplettes Inventar des Haushalts |
| `GET` | `/api/inventory/<id>` | Einzelner Inventar-Artikel |
| `GET` | `/api/inventory/<id>/history` | Änderungshistorie eines Artikels (inkl. Benutzer) |
| `GET` | `/api/shopping` | Offene Einkaufsliste des Haushalts |

### Beispiel mit curl

```bash
# 1. Token anfordern
curl -X POST https://<host>/api/login \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"max\", \"password\": \"meinpasswort\"}"

# 2. Inventar abrufen (Token einsetzen)
curl https://<host>/api/inventory \
  -H "Authorization: Bearer <access_token>"
```

---

## 🔒 Sicherheit

- Passwörter werden ausschliesslich als Hash gespeichert (Werkzeug `generate_password_hash`).
- CSRF-Schutz für alle Web-Formulare (Flask-WTF). Das API ist davon ausgenommen, da es Token-basiert arbeitet.
- Passwort-Mindestlänge von 8 Zeichen bei der Registrierung.
- Session-Cookies mit `HttpOnly` und `SameSite=Lax`.
- Zugriffskontrolle: Benutzer sehen und ändern ausschliesslich Daten ihres eigenen Haushalts.

---

## 🗄️ Datenmodell (Kurzüberblick)

- **Household** – ein Haushalt (Familie) mit eindeutigem Einladungscode.
- **User** – ein Familienmitglied, gehört zu genau einem Haushalt.
- **InventoryItem** – ein Vorratsartikel, gehört zu einem Haushalt.
- **ShoppingItem** – ein Eintrag auf der Einkaufsliste, gehört zu einem Haushalt.
- **StockChange** – ein Eintrag in der Bestandshistorie (verweist auf Artikel und Benutzer).

---

## 📝 Lizenz / Hinweis

Dieses Projekt wurde als Praxisarbeit im Rahmen der ipso Bildung erstellt.
