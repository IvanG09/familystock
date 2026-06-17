import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    
    # Sicherheits-Einstellungen für das Session-Cookie
    SESSION_COOKIE_HTTPONLY = True   # Cookie nicht per JavaScript lesbar (Schutz vor XSS)
    SESSION_COOKIE_SAMESITE = 'Lax'  # Schutz gegen Cross-Site-Anfragen