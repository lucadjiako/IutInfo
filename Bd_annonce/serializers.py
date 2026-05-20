from rest_framework import serializers
from .models import Annonce, PieceJointe, Lecture


class PieceJointeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PieceJointe
        fields = ['id', 'fichier', 'nom_fichier', 'taille']
        read_only_fields = ['nom_fichier', 'taille']


# ── LISTE : informations résumées ──────────────────────────
class AnnonceListSerializer(serializers.ModelSerializer):
    """Serializer léger pour la liste des annonces."""
    auteur_nom  = serializers.SerializerMethodField()
    est_lu      = serializers.SerializerMethodField()
    est_visible = serializers.SerializerMethodField()

    class Meta:
        model  = Annonce
        fields = [
            'id',
            'titre',
            'auteur_nom',
            'role_cible',
            'date_publication',
            'date_expiration',
            'est_visible',
            'est_lu',
        ]

    def get_auteur_nom(self, obj):
        return f"{obj.auteur.nom} {obj.auteur.prenom}".strip()

    def get_est_lu(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Lecture.objects.filter(
            annonce=obj,
            utilisateur=request.user
        ).exists()

    def get_est_visible(self, obj):
        return obj.est_visible()


# ── DÉTAIL : informations complètes ────────────────────────
class AnnonceDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour le détail d'une annonce."""
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)
    auteur_nom     = serializers.SerializerMethodField()
    est_lu         = serializers.SerializerMethodField()
    est_visible    = serializers.SerializerMethodField()

    class Meta:
        model  = Annonce
        fields = [
            'id',
            'titre',
            'contenu',
            'auteur',
            'auteur_nom',
            'role_cible',
            'filiere_cible',
            'niveau_cible',
            'date_creation',
            'date_publication',
            'date_expiration',
            'est_visible',
            'pieces_jointes',
            'est_lu',
        ]
        read_only_fields = ['auteur', 'date_creation']

    def get_auteur_nom(self, obj):
        return f"{obj.auteur.nom} {obj.auteur.prenom}".strip()

    def get_est_lu(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Lecture.objects.filter(
            annonce=obj,
            utilisateur=request.user
        ).exists()

    def get_est_visible(self, obj):
        return obj.est_visible()


# ── CRÉATION / MODIFICATION ─────────────────────────────────
class AnnonceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Annonce
        fields = [
            'titre',
            'contenu',
            'role_cible',
            'filiere_cible',
            'niveau_cible',
            'date_publication',
            'date_expiration',
          
        ]

    def validate(self, data):
        pub = data.get('date_publication')
        exp = data.get('date_expiration')
        if pub and exp and exp <= pub:
            raise serializers.ValidationError(
                {"date_expiration": "La date d'expiration doit être après la date de publication."}
            )
        return data