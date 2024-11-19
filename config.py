import pyrebase
import firebase_admin
from firebase_admin import credentials

FIREBASE_CONFIG = {
    "apiKey": "",
    "authDomain": "",
    "databaseURL": "",
    "storageBucket": "",
}

EMAIL_CONFIG = {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "",
    "sender_password": ""  # Replace with an App Password if using Gmail with 2FA
}

SERVICE_ACCOUNT_PATH = 'serviceAccountKey.json'

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_CONFIG['databaseURL']
    })

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()
