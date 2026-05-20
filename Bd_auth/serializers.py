from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import Utilisateur


# ──────────────────────────────────────────────
#  ÉTAPE 1 — Vérification matricule / email
# ──────────────────────────────────────────────
class ActivationSerializer(serializers.Serializer):
    """
    L'utilisateur entre son matricule ET/OU son email.
    On accepte les deux : l'un ou l'autre suffit pour identifier.
    """
    matricule = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email     = serializers.EmailField(required=False, allow_blank=True)

    def validate(self, data):
        matricule = data.get('matricule', '').strip()
        email     = data.get('email', '').strip()
        if not matricule and not email:
            raise serializers.ValidationError(
                "Fournissez au moins votre matricule ou votre email."
            )
        return data


# ──────────────────────────────────────────────
#  ÉTAPE 2 — Création du mot de passe
# ──────────────────────────────────────────────
class SetPasswordSerializer(serializers.Serializer):
    email            = serializers.EmailField()
    password         = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Les mots de passe ne correspondent pas."}
            )
        validate_password(data['password'])
        return data


# ──────────────────────────────────────────────
#  ÉTAPE 3 — Vérification OTP
# ──────────────────────────────────────────────
class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code  = serializers.CharField(max_length=6, min_length=6)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Le code OTP doit être composé de 6 chiffres.")
        return value


# ──────────────────────────────────────────────
#  LOGIN (connexions suivantes)
# ──────────────────────────────────────────────
class LoginSerializer(serializers.Serializer):
    """
    Accepte matricule OU email + mot de passe.
    """
    identifiant = serializers.CharField(
        help_text="Matricule ou adresse email"
    )
    password = serializers.CharField(write_only=True)


# ──────────────────────────────────────────────
#  RESEND OTP
# ──────────────────────────────────────────────
class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ──────────────────────────────────────────────
#  PROFIL
# ──────────────────────────────────────────────
class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Utilisateur
        fields = [
            'id', 'matricule', 'email', 'nom', 'prenom', 'role',
            'filiere', 'niveau', 'departement', 'specialite',
            'active', 'is_staff', 'created_at', 'updated_at','numero_telephone'
        ]
        read_only_fields = fields  # lecture seule — modification via endpoint dédié


# ──────────────────────────────────────────────
#  CRÉER UN ADMIN (par un admin existant)
# ──────────────────────────────────────────────
class CreateAdminSerializer(serializers.Serializer):
    matricule = serializers.CharField(max_length=20)
    email     = serializers.EmailField()
    nom       = serializers.CharField(max_length=100)
    prenom    = serializers.CharField(max_length=100, required=False, default='')

    def validate_matricule(self, value):
        if Utilisateur.objects.filter(matricule=value).exists():
            raise serializers.ValidationError("Ce matricule est déjà utilisé.")
        return value

    def validate_email(self, value):
        if Utilisateur.objects.filter(email=value).exists():
            raise serializers.ValidationError("Cet email est déjà utilisé.")
        return value