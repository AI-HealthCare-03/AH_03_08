import firebase_admin
from firebase_admin import credentials

_initialized = False

def get_firebase_app():
    global _initialized
    if not _initialized:
        cred = credentials.Certificate("envs/firebase-service-account.json")
        firebase_admin.initialize_app(cred)
        _initialized = True
    return firebase_admin.get_app()