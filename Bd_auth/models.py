from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from datetime import timedelta


# ──────────────────────────────────────────────
#  MANAGER PERSONNALISÉ
# ──────────────────────────────────────────────
class UtilisateurManager(BaseUserManager):

    def create_user(self, matricule, email, password=None, **extra_fields):
        if not matricule:
            raise ValueError("Le matricule est obligatoire")
        if not email:
            raise ValueError("L'email est obligatoire")
        email = self.normalize_email(email)
        user = self.model(matricule=matricule, email=email, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, matricule, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('active', True)
        extra_fields.setdefault('role', 'admin')
        return self.create_user(matricule, email, password, **extra_fields)


# ──────────────────────────────────────────────
#  MODÈLE UTILISATEUR
# ──────────────────────────────────────────────
class Utilisateur(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ('etudiant',   'Étudiant'),
        ('professeur', 'Professeur'),
        ('admin',      'Administrateur'),
    )

    # ── Identifiants ──────────────────────────
    matricule = models.CharField(max_length=20, unique=True)
    email     = models.EmailField(unique=True)

    # ── Informations personnelles ─────────────
    nom    = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True, default='')
    role   = models.CharField(max_length=20, choices=ROLE_CHOICES, default='etudiant')

    # ── Champs Étudiant ───────────────────────
    filiere = models.CharField(max_length=100, blank=True, null=True)
    niveau  = models.CharField(max_length=10,  blank=True, null=True)

    # ── Champs Professeur ─────────────────────
    departement = models.CharField(max_length=100, blank=True, null=True)
    specialite  = models.CharField(max_length=100, blank=True, null=True)

    # ── Statut ────────────────────────────────
    active       = models.BooleanField(default=False)   # compte activé par OTP
    is_staff     = models.BooleanField(default=False)   # accès admin Django
    is_superuser = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    token_fcm = models.CharField(max_length=255, blank=True, null=True)
    
    numero_telephone = models.CharField(
    max_length=20,
    blank=True,
    null=True,
    verbose_name="Numéro de téléphone")

    # ── Config AbstractBaseUser ───────────────
    USERNAME_FIELD  = 'matricule'          # champ principal d'identification
    REQUIRED_FIELDS = ['email', 'nom']

    objects = UtilisateurManager()

    class Meta:
        ordering  = ['-created_at']
        verbose_name = 'Utilisateur'

    def __str__(self):
        return f"{self.matricule} — {self.nom} {self.prenom} ({self.role})"

    @property
    def is_active(self):
        """Django utilise is_active pour bloquer la connexion."""
        return self.active

    @property
    def is_admin(self):
        return self.is_staff or self.role == 'admin'


# ──────────────────────────────────────────────
#  OTP
# ──────────────────────────────────────────────
class OTP(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur, on_delete=models.CASCADE, related_name='otps'
    )
    code       = models.CharField(max_length=6)
    is_valid   = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_expired(self):
        """OTP valide pendant 10 minutes."""
        return timezone.now() > self.created_at + timedelta(minutes=10)

    def __str__(self):
        return f"OTP {self.code} → {self.utilisateur.email}"