import random
from django.core.mail import send_mail
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Utilisateur, OTP
from .serializers import ActivationSerializer
from rest_framework_simplejwt.tokens import RefreshToken

# Create your views here.

class ActivationCompte(APIView):
    def post(self, request):
        serializer = ActivationSerializer(data = request.data)
        serializer.is_valid(raise_exception=True)
        data= serializer.validated_data
        
        try:
            utilisateur= Utilisateur.objects.get(
                matricule= data["matricule"],
                nom= data["nom"],
                prenom = data["prenom"]
            )
            
        except Utilisateur.DoesNotExist:
            return Response(
                { "message": "Acces refusé: utilisateuer non reconnu."},
                status= status.HTTP_403_FORBIDDEN
            )
        
        if utilisateur.active:
            return Response(
                {"message": "Compte déjà activé."},
                status=status.HTTP_400_BAD_REQUEST
            )
        utilisateur.set_password(data["mot_de_passe"])
        utilisateur.active = True
        utilisateur.save()

        refresh = RefreshToken.for_user(utilisateur)

        return Response({
            "message": "Compte activé avec succès.",
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })

class Login(APIView):

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=400)

        if not user.check_password(password):
            return Response({"error": "Mot de passe incorrect"}, status=400)

        if not user.active:
            return Response({"error": "Compte non activé"}, status=403)

        #  génération OTP
        code = str(random.randint(100000, 999999))

        OTP.objects.create(utilisateur=user, code=code)

        # envoi email
        send_mail(
            "Votre code OTP",
            f"Votre code est : {code}",
            "campusinfo@gmail.com",  # expéditeur (ton app)
            [user.email],       # destinataire (utilisateur)
        )

        return Response({"message": "Code envoyé par email"})
    
class Verification_OTP(APIView):

    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")

        try:
            user = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response({"error": "Utilisateur introuvable"}, status=400)

        otp = OTP.objects.filter(
            utilisateur=user,
            code=code,
            is_valid=True
        ).last()

        if not otp:
            return Response({"error": "Code invalide"}, status=400)

        if otp.is_expired():
            return Response({"error": "Code expiré"}, status=400)

        otp.is_valid = False
        otp.save()

        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })