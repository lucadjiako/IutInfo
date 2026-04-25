from rest_framework import serializers
from .models import Annonce, PieceJointe, Lecture


class PieceJointeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PieceJointe
        fields = ["id", "fichier"]


class AnnonceSerializer(serializers.ModelSerializer):
    pieces_jointes = PieceJointeSerializer(many=True, read_only=True)
    est_lu = serializers.SerializerMethodField()

    class Meta:
        model = Annonce
        fields = [
            "id",
            "titre",
            "contenu",
            "date_creation",
            "date_publication",
            "auteur",
            "role_cible",
            "filiere_cible",
            "niveau_cible",
            "pieces_jointes",
            "est_lu",
        ]

    def get_est_lu(self, obj):
        user = self.context["request"].user
        return Lecture.objects.filter(
            annonce=obj,
            utilisateur=user
        ).exists()
