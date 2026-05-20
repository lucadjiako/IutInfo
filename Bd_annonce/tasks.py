from django.utils import timezone
from datetime import timedelta
from .models import Annonce

BATCH_SIZE = 100  # supprimer 100 annonces à la fois max


def archiver_annonces_expirees():
    """Archive toutes les annonces dont la date d'expiration est dépassée."""
    maintenant = timezone.now()
    annonces = Annonce.objects.filter(
        date_expiration__lt=maintenant,
        statut='active'
    )
    count = annonces.update(
        statut='archivee',
        date_archivage=maintenant
    )
    print(f"[Scheduler] {count} annonce(s) archivée(s).")


def supprimer_annonces_archivees():
    """Supprime par batch les annonces archivées depuis plus de 30 jours."""
    limite = timezone.now() - timedelta(days=30)
    annonces = Annonce.objects.filter(
        statut='archivee',
        date_archivage__lt=limite
    )[:BATCH_SIZE]

    ids = list(annonces.values_list('id', flat=True))
    if ids:
        Annonce.objects.filter(id__in=ids).delete()
        print(f"[Scheduler] {len(ids)} annonce(s) supprimée(s).")
    else:
        print("[Scheduler] Aucune annonce à supprimer.")