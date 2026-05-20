import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _normaliser_numero(numero: str) -> str | None:
    """
    Normalise un numéro camerounais vers le format E.164 international.
    Exemples :
        "699123456"   → "+237699123456"
        "0699123456"  → "+237699123456"
        "+237699123456" → "+237699123456"
    """
    if not numero:
        return None
    numero = numero.strip().replace(" ", "").replace("-", "")
    if numero.startswith("+237"):
        return numero
    if numero.startswith("237"):
        return "+" + numero
    if numero.startswith("0"):
        return "+237" + numero[1:]
    if len(numero) == 9:
        return "+237" + numero
    return None


def envoyer_sms(numero: str, message: str) -> bool:
    """
    Envoie un SMS via Twilio (Orange + MTN + Camtel).
    En mode sandbox, logue seulement sans appel réseau.
    Retourne True si succès, False sinon.
    """
    numero_normalise = _normaliser_numero(numero)
    if not numero_normalise:
        logger.warning(f"Numéro invalide ignoré : {numero}")
        return False

    # ── Mode Sandbox ──────────────────────────────────────────
    if settings.SMS_SANDBOX:
        print(f"\n📱 [SMS SANDBOX]")
        print(f"   Vers    : {numero_normalise}")
        print(f"   Message : {message}\n")
        logger.info(f"[SMS SANDBOX] → {numero_normalise} | {message}")
        return True

    # ── Mode Production (Twilio) ──────────────────────────────
    try:
        from twilio.rest import Client
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=message,
            from_=settings.TWILIO_PHONE_NUMBER,
            to=numero_normalise,
        )
        logger.info(f"SMS envoyé → {numero_normalise} | SID : {msg.sid}")
        return True

    except Exception as e:
        logger.error(f"Échec SMS → {numero_normalise} | Erreur : {e}")
        return False


def envoyer_sms_urgent(annonce) -> dict:
    """
    Envoie un SMS URGENT à tous les utilisateurs actifs
    ayant un numéro de téléphone enregistré.
    Retourne un dict résumant les résultats.
    """
    from Bd_auth.models import Utilisateur

    utilisateurs = Utilisateur.objects.filter(
        is_active=True,
        numero_telephone__isnull=False,
    ).exclude(numero_telephone="")

    message = (
        f"[CampusInfo - URGENT]\n"
        f"{annonce.titre}\n"
        f"{annonce.contenu[:120]}{'...' if len(annonce.contenu) > 120 else ''}"
    )

    resultats = {"total": 0, "succes": 0, "echecs": 0}

    for user in utilisateurs:
        resultats["total"] += 1
        ok = envoyer_sms(user.numero_telephone, message)
        if ok:
            resultats["succes"] += 1
        else:
            resultats["echecs"] += 1

    logger.info(
        f"SMS URGENT '{annonce.titre}' — "
        f"{resultats['succes']}/{resultats['total']} envoyés"
    )
    return resultats