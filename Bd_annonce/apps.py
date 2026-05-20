from django.apps import AppConfig


class BdAnnonceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Bd_annonce'

    def ready(self):
        from apscheduler.schedulers.background import BackgroundScheduler
        from .tasks import archiver_annonces_expirees, supprimer_annonces_archivees

        scheduler = BackgroundScheduler()

        # Toutes les heures
        scheduler.add_job(archiver_annonces_expirees, 'interval', hours=1)

        # Toutes les 24h
        scheduler.add_job(supprimer_annonces_archivees, 'interval', hours=24)

        scheduler.start()