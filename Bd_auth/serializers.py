from rest_framework import serializers

class ActivationSerializer(serializers.Serializer):
    matricule = serializers.CharField()
    nom = serializers.CharField()
    prenom = serializers.CharField()
    mot_de_passe= serializers.CharField(min_length=6)
    