# from rest_framework import generics
# from rest_framework.permissions import IsAuthenticated
# from django.utils import timezone
# from .models import Annonce
# from .serializers import AnnonceSerializer


# class AnnonceListView(generics.ListAPIView):
#     serializer_class = AnnonceSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         user = self.request.user
#         maintenant = timezone.now()

#         # Admin voit tout
#         if user.is_superuser:
#             return Annonce.objects.filter(
#                 date_publication__lte=maintenant
#             )

#         # Autres voient seulement leur rôle
#         return Annonce.objects.filter(
#             role_cible=user.role,
#             date_publication__lte=maintenant
#         )
        
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q
from .models import Annonce, Lecture
from .serializers import AnnonceSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404



class Marquer_lu(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        annonce = get_object_or_404(Annonce, pk=pk)

        Lecture.objects.get_or_create(
            utilisateur=request.user,
            annonce=annonce
        )

        return Response({"message": "Annonce marquée comme lue"})


class AnnonceDetail(APIView):
    
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        annonce = get_object_or_404(Annonce, pk=pk)
        serializer = AnnonceSerializer(annonce)
        return Response(serializer.data)

    def put(self, request, pk):
        annonce = get_object_or_404(Annonce, pk=pk)

        if (
            request.user != annonce.author
            and not request.user.is_staff
        ):
            return Response({"error": "Non autorisé"}, status=403)

        serializer = AnnonceSerializer(annonce, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)

        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        annonce = get_object_or_404(Annonce, pk=pk)

        if (
            request.user != annonce.author
            and not request.user.is_staff
        ):
            return Response({"error": "Non autorisé"}, status=403)

        annonce.delete()
        return Response(status=204)

class AnnonceList(generics.ListAPIView):
    serializer_class = AnnonceSerializer
    permission_classes = [IsAuthenticated]


    def get_queryset(self):
        user = self.request.user
        now = timezone.now()

        # On prend seulement les annonces déjà publiées
        queryset = Annonce.objects.filter(
            date_publication__lte=now
        )

        # Si admin → il voit tout
        if user.role.role.lower() == "administrateur":
            return queryset

        # Filtrage par rôle
        queryset = queryset.filter(role_cible=user.role)

        # Si étudiant → filtrage filière + niveau
        if user.role.role.lower() == "etudiant":

            queryset = queryset.filter(
                Q(filiere_cible=user.filiere) | Q(filiere_cible__isnull=True),
                Q(niveau_cible=user.niveau) | Q(niveau_cible__isnull=True)
            )

        return queryset


''