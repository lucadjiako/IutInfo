from django.db import models
from django.conf import settings
from django.utils import timezone


class Annonce(models.Model):

    ROLE_CIBLE_CHOICES = (
        ('tous',       'Tout le campus'),
        ('etudiant',   'Étudiants'),
        ('professeur', 'Professeurs'),
    )

    titre           = models.CharField(max_length=255)
    contenu         = models.TextField()
    auteur          = models.ForeignKey(
                          settings.AUTH_USER_MODEL,
                          on_delete=models.CASCADE,
                          related_name='annonces'
                      )

    # ── Ciblage ───────────────────────────────────────────────
    role_cible      = models.CharField(
                          max_length=20,
                          choices=ROLE_CIBLE_CHOICES,
                          default='tous'
                      )
    filiere_cible   = models.CharField(max_length=100, blank=True, null=True,
                          help_text="Laisser vide = toutes les filières")
    niveau_cible    = models.CharField(max_length=10,  blank=True, null=True,
                          help_text="Laisser vide = tous les niveaux")

    # ── Dates ─────────────────────────────────────────────────
    date_creation   = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(
                          default=timezone.now,
                          help_text="Date/heure de publication (peut être dans le futur)"
                      )
    date_expiration  = models.DateTimeField(
                          blank=True, null=True,
                          help_text="Laisser vide = jamais expirée"
                      )
    
    numero_telephone = models.CharField(
    max_length=20,
    blank=True,
    null=True,
    verbose_name="Numéro de téléphone"
)
    
    # ── Archivage ─────────────────────────────────────────────
    STATUT_CHOICES = (
        ('active',   'Active'),
        ('archivee', 'Archivée'),
    )
    statut         = models.CharField(
                        max_length=20,
                        choices=STATUT_CHOICES,
                        default='active'
                    )
    date_archivage = models.DateTimeField(
                        blank=True, null=True,
                        help_text="Date à laquelle l'annonce a été archivée"
                    )

    class Meta:
        ordering = ['-date_publication']

    def __str__(self):
        return self.titre

    def est_publiee(self):
        return self.date_publication <= timezone.now()

    def est_expiree(self):
        if self.date_expiration is None:
            return False
        return timezone.now() > self.date_expiration

    def est_visible(self):
        return self.est_publiee() and not self.est_expiree()


class PieceJointe(models.Model):
    annonce = models.ForeignKey(
        Annonce, on_delete=models.CASCADE, related_name='pieces_jointes'
    )
    fichier    = models.FileField(upload_to='annonces/pieces_jointes/')
    nom_fichier = models.CharField(max_length=255, blank=True)
    taille      = models.PositiveIntegerField(default=0, help_text="Taille en octets")

    def save(self, *args, **kwargs):
        if self.fichier and not self.nom_fichier:
            self.nom_fichier = self.fichier.name
        if self.fichier and not self.taille:
            self.taille = self.fichier.size
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom_fichier} → {self.annonce.titre}"


class Lecture(models.Model):
    annonce     = models.ForeignKey(
                      Annonce,
                      on_delete=models.CASCADE,
                      related_name='lectures'
                  )
    utilisateur = models.ForeignKey(
                      settings.AUTH_USER_MODEL,
                      on_delete=models.CASCADE,
                      related_name='lectures'
                  )
    lu_a        = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('annonce', 'utilisateur')
        ordering        = ['-lu_a']

    def __str__(self):
        return f"{self.utilisateur.matricule} a lu « {self.annonce.titre} »"
    
