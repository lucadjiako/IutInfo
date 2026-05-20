from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.utils import timezone
from rest_framework import generics

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from .models import Annonce, PieceJointe, Lecture
from .firebase import envoyer_notification_multiple
from Bd_auth.models import Utilisateur
 
from .serializers import (
    AnnonceListSerializer,
    AnnonceDetailSerializer,
    AnnonceCreateSerializer,
    AnnonceCreateSerializer,

    
)


# ──────────────────────────────────────────────
#  PERMISSIONS PERSONNALISÉES
# ──────────────────────────────────────────────

def _est_admin(user):
    return user.is_staff or user.role == 'admin'

def _est_professeur(user):
    return user.role == 'professeur'

def _peut_modifier(user, annonce):
    """Seul l'auteur ou un admin peut modifier/supprimer."""
    return _est_admin(user) or user == annonce.auteur


# ──────────────────────────────────────────────
#  FILTRAGE INTELLIGENT DES ANNONCES
# ──────────────────────────────────────────────

def _get_annonces_visibles(user):
    """
    Retourne le queryset des annonces visibles selon le rôle :
    - Admin       → toutes les annonces (publiées ou non)
    - Professeur  → annonces ciblant 'tous' ou 'professeur'
    - Étudiant    → annonces ciblant 'tous' ou 'etudiant',
                    filtrées par sa filière et son niveau
    """
    now = timezone.now()

    if _est_admin(user):
        # L'admin voit tout, y compris les annonces futures et expirées
        return Annonce.objects.all()

    # Base : annonces publiées et non expirées
    qs = Annonce.objects.filter(
        date_publication__lte=now
    ).filter(
        Q(date_expiration__isnull=True) | Q(date_expiration__gt=now)
    )

    if _est_professeur(user):
        return qs.filter(role_cible__in=['tous', 'professeur'])

    # Étudiant
    qs = qs.filter(role_cible__in=['tous', 'etudiant'])

    # Filtre filière (si l'annonce cible une filière précise)
    if user.filiere:
        qs = qs.filter(
            Q(filiere_cible__isnull=True) | Q(filiere_cible=user.filiere)
        )

    # Filtre niveau (si l'annonce cible un niveau précis)
    if user.niveau:
        qs = qs.filter(
            Q(niveau_cible__isnull=True) | Q(niveau_cible=user.niveau)
        )

    return qs


# ──────────────────────────────────────────────
#  LISTE + CRÉATION
# ──────────────────────────────────────────────

class AnnonceList(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        """
        GET /api/annonces/
        Retourne les annonces filtrées selon le rôle de l'utilisateur.
        """
        qs = _get_annonces_visibles(request.user)

        # Filtres optionnels via query params
        filiere = request.query_params.get('filiere')
        niveau  = request.query_params.get('niveau')
        role    = request.query_params.get('role_cible')

        if filiere:
            qs = qs.filter(filiere_cible=filiere)
        if niveau:
            qs = qs.filter(niveau_cible=niveau)
        if role:
            qs = qs.filter(role_cible=role)

        q = request.query_params.get('q')
        
        if q: ## recherche texte dans le titre ou le contenu
            qs = qs.filter(
                 Q(titre__icontains=q) |
                Q(contenu__icontains=q)
                )

        serializer = AnnonceListSerializer(qs, many=True, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
    # """
    # POST /api/annonces/
    # Créer une annonce (professeur ou admin uniquement).
    # Pièces jointes : envoyer en multipart avec le champ 'fichiers'.
    # """
        if not (_est_admin(request.user) or _est_professeur(request.user)):
            return Response(
                {"error": "Seuls les professeurs et les administrateurs peuvent créer des annonces."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AnnonceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        annonce = serializer.save(auteur=request.user)

        # Gestion des pièces jointes
        fichiers = request.FILES.getlist('fichiers')
        for f in fichiers:
            if f.size > 10 * 1024 * 1024:  # 10 MB max
                continue
            PieceJointe.objects.create(
                annonce=annonce,
                fichier=f,
                nom_fichier=f.name,
                taille=f.size,
            )

        # ── FCM : en dehors du for ──────────────────────────
        tokens = list(
            Utilisateur.objects.filter(
                token_fcm__isnull=False
            ).exclude(
                token_fcm=''
            ).values_list('token_fcm', flat=True)
        )

        envoyer_notification_multiple(
            tokens=tokens,
            titre=annonce.titre,
            corps=f"Nouvelle annonce : {annonce.contenu[:100]}",
            data={"annonce_id": str(annonce.id)}
        )
        # ── SMS si annonce URGENTE (Orange + MTN + Camtel) ────────────
        if serializer.instance.priorite == "URGENT":
            from .sms import envoyer_sms_urgent
            resultats_sms = envoyer_sms_urgent(serializer.instance)
            logger.info(
                f"SMS URGENT : {resultats_sms['succes']} succès / "
                f"{resultats_sms['echecs']} échecs sur "
                f"{resultats_sms['total']} destinataires"
            )
        # ────────────────────────────────────────────────────

        return Response(
            AnnonceDetailSerializer(annonce, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )


# ──────────────────────────────────────────────
#  DÉTAIL + MODIFICATION + SUPPRESSION
# ──────────────────────────────────────────────

class AnnonceDetail(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def _get_annonce(self, pk, user):
        """Retourne l'annonce si elle est accessible pour cet utilisateur."""
        if _est_admin(user):
            return get_object_or_404(Annonce, pk=pk)
        qs = _get_annonces_visibles(user)
        return get_object_or_404(qs, pk=pk)

    def get(self, request, pk):
        """GET /api/annonces/{id}/"""
        annonce    = self._get_annonce(pk, request.user)
        serializer = AnnonceDetailSerializer(annonce, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """PUT /api/annonces/{id}/ — modification partielle autorisée"""
        annonce = get_object_or_404(Annonce, pk=pk)

        if not _peut_modifier(request.user, annonce):
            return Response(
                {"error": "Vous n'êtes pas autorisé à modifier cette annonce."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AnnonceCreateSerializer(
            annonce, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        annonce = serializer.save()

        return Response(
            AnnonceDetailSerializer(annonce, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def delete(self, request, pk):
        """DELETE /api/annonces/{id}/"""
        annonce = get_object_or_404(Annonce, pk=pk)

        if not _peut_modifier(request.user, annonce):
            return Response(
                {"error": "Vous n'êtes pas autorisé à supprimer cette annonce."},
                status=status.HTTP_403_FORBIDDEN
            )

        annonce.delete()
        return Response(
            {"message": "Annonce supprimée avec succès."},
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  MARQUER COMME LU
# ──────────────────────────────────────────────

class MarquerLu(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        """POST /api/annonces/{id}/lu/"""
        annonce = get_object_or_404(Annonce, pk=pk)
        lecture, created = Lecture.objects.get_or_create(
            annonce=annonce,
            utilisateur=request.user,
        )
        return Response(
            {
                "message":  "Annonce marquée comme lue.",
                "premiere_lecture": created,
                "lu_a":     lecture.lu_a,
            },
            status=status.HTTP_200_OK
        )
# ──────────────────────────────────────────────
#  BOÎTE DES ANNONCES ARCHIVÉES
# ──────────────────────────────────────────────

class AnnonceArchiveeList(generics.ListAPIView):
        permission_classes = [IsAuthenticated]
        serializer_class   = AnnonceDetailSerializer

        def get_queryset(self):
            if not _est_admin(self.request.user):
                return Annonce.objects.none()
            return Annonce.objects.filter(
                statut='archivee'
            ).order_by('-date_archivage')

# ──────────────────────────────────────────────
#  STATISTIQUES (admin uniquement)
# ──────────────────────────────────────────────

class AnnonceStats(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """
        GET /api/annonces/{id}/stats/
        Nombre de lectures + liste des lecteurs (admin seulement).
        """
        if not _est_admin(request.user):
            return Response(
                {"error": "Accès réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )

        annonce  = get_object_or_404(Annonce, pk=pk)
        lectures = Lecture.objects.filter(annonce=annonce).select_related('utilisateur')

        lecteurs = [
            {
                "matricule": l.utilisateur.matricule,
                "nom":       f"{l.utilisateur.nom} {l.utilisateur.prenom}".strip(),
                "lu_a":      l.lu_a,
            }
            for l in lectures
        ]

        return Response(
            {
                "annonce_id":     annonce.id,
                "titre":          annonce.titre,
                "total_lectures": len(lecteurs),
                "lecteurs":       lecteurs,
            },
            status=status.HTTP_200_OK
        )
        
