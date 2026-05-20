import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings

# Initialisation unique de Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)


def envoyer_notification(token, titre, corps, data=None):
    """
    Envoie une notification push à un seul appareil.
    token  : token FCM de l'utilisateur
    titre  : titre de la notification
    corps  : message de la notification
    data   : dict optionnel de données supplémentaires
    """
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=titre,
                body=corps,
            ),
            data=data or {},
            token=token,
        )
        response = messaging.send(message)
        print(f"[FCM] Notification envoyée : {response}")
        return True
    except Exception as e:
        print(f"[FCM] Erreur : {e}")
        return False


def envoyer_notification_multiple(tokens, titre, corps, data=None):
    """
    Envoie une notification push à plusieurs appareils.
    tokens : liste de tokens FCM
    """
    if not tokens:
        return

    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=titre,
            body=corps,
        ),
        data=data or {},
        tokens=tokens,
    )

    response = messaging.send_each_for_multicast(message)
    print(f"[FCM] {response.success_count} envoyés, {response.failure_count} échoués.")
    return response