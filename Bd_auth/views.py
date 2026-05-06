import random
import csv
import xml.etree.ElementTree as ET
from io import TextIOWrapper, StringIO

from django.core.mail import send_mail
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.db.models import Q

from .models import Utilisateur, OTP
from .serializers import (
    # ActivationSerializer,
    # SetPasswordSerializer,
    VerifyOTPSerializer,
    LoginSerializer,
    ResendOTPSerializer,
    UserProfileSerializer,
    CreateAdminSerializer,
)


# ──────────────────────────────────────────────
#  UTILITAIRES
# ──────────────────────────────────────────────

def _generer_otp(utilisateur):
    """Invalide les anciens OTP et génère un nouveau."""
    OTP.objects.filter(utilisateur=utilisateur, is_valid=True).update(is_valid=False)
    code = str(random.randint(100000, 999999))
    OTP.objects.create(utilisateur=utilisateur, code=code)
    return code


def _envoyer_otp_email(email, code, sujet="Code de vérification IUT"):
    send_mail(
        subject=sujet,
        message=(
            f"Votre code de vérification est : {code}\n\n"
            f"Ce code expire dans 10 minutes.\n"
            f"Ne partagez ce code avec personne."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )


def _generer_tokens(utilisateur):
    """Retourne access + refresh JWT pour un utilisateur."""
    refresh = RefreshToken.for_user(utilisateur)
    return {
        "access":  str(refresh.access_token),
        "refresh": str(refresh),
    }


def _user_data(utilisateur):
    return {
        "matricule": utilisateur.matricule,
        "email":     utilisateur.email,
        "nom":       utilisateur.nom,
        "prenom":    utilisateur.prenom,
        "role":      utilisateur.role,
        "is_staff":  utilisateur.is_staff,
    }


# ──────────────────────────────────────────────
#  ÉTAPE 1 — Vérification + Password + Envoi OTP
# ──────────────────────────────────────────────
class Activation(APIView):
    """
    POST /api/auth/activation/
    Body: { 
        "identifiant": "matricule ou email", 
        "password": "...", 
        "password_confirm": "..." 
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        identifiant      = request.data.get('identifiant', '').strip()
        password         = request.data.get('password', '')
        password_confirm = request.data.get('password_confirm', '')

        if not identifiant:
            return Response(
                {"error": "Le matricule ou l'email est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not password or not password_confirm:
            return Response(
                {"error": "Le mot de passe est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if password != password_confirm:
            return Response(
                {"error": "Les mots de passe ne correspondent pas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Recherche par matricule ou email
        try:
            if '@' in identifiant:
                utilisateur = Utilisateur.objects.get(email=identifiant)
            else:
                utilisateur = Utilisateur.objects.get(matricule=identifiant)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": "Compte introuvable. Contactez l'administrateur."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Compte déjà activé
        if utilisateur.active:
            return Response(
                {
                    "error": "Compte déjà activé.",
                    "next_step": "login",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sauvegarde temporaire du mot de passe hashé
        utilisateur.set_password(password)
        utilisateur.save()

        # Génère et envoie l'OTP
        code = _generer_otp(utilisateur)
        _envoyer_otp_email(
            utilisateur.email, 
            code, 
            "Activation de votre compte IUT"
        )

        return Response(
            {
                "message": "Un code OTP a été envoyé à votre email.",
                "email":   utilisateur.email,
                "next_step": "verify_otp",
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  ÉTAPE 2 — Vérification OTP → Activation
# ──────────────────────────────────────────────
class VerifyOTP(APIView):
    """
    POST /api/auth/verify-otp/
    Body: { "email": "...", "code": "123456" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip()
        code  = request.data.get('code', '').strip()

        if not email or not code:
            return Response(
                {"error": "Email et code OTP requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            utilisateur = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        otp = OTP.objects.filter(
            utilisateur=utilisateur,
            code=code,
            is_valid=True
        ).last()

        if not otp:
            return Response(
        {
            "error": "Code OTP invalide.",
            "can_resend": True,  # Le frontend affiche le bouton "Renvoyer le code"
        },
        status=status.HTTP_400_BAD_REQUEST
    )

        if otp.is_expired():
            return Response(
        {
            "error": "Code OTP expiré.",
            "can_resend": True,  # Le frontend affiche le bouton "Renvoyer le code"
        },
        status=status.HTTP_400_BAD_REQUEST
    )
        # Invalide l'OTP
        otp.is_valid = False
        otp.save()

        # Active le compte — le password est déjà enregistré depuis l'étape 1
        utilisateur.active = True
        utilisateur.save()

        tokens = _generer_tokens(utilisateur)

        return Response(
            {
                "message": "Compte activé avec succès. Bienvenue !",
                **tokens,
                "user": _user_data(utilisateur),
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  ÉTAPE 3 — Vérification OTP → activation + JWT
# ──────────────────────────────────────────────
class VerifyOTP(APIView):
    """
    POST /api/auth/verify-otp/
    Body: { "email": "...", "code": "123456" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            utilisateur = Utilisateur.objects.get(email=data['email'])
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        otp = OTP.objects.filter(
            utilisateur=utilisateur,
            code=data['code'],
            is_valid=True
        ).last()

        if not otp:
            return Response(
                {
                    "error": "Code OTP invalide.",
                    "hint":  "Utilisez POST /api/auth/resend-otp/ pour recevoir un nouveau code.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        if otp.is_expired():
            return Response(
                {
                    "error": "Code OTP expiré.",
                    "hint":  "Utilisez POST /api/auth/resend-otp/ pour recevoir un nouveau code.",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Marque l'OTP comme utilisé
        otp.is_valid = False
        otp.save()

        # Active le compte
        utilisateur.active = True
        utilisateur.save()

        tokens = _generer_tokens(utilisateur)

        return Response(
            {
                "message": "Compte activé avec succès. Bienvenue !",
                **tokens,
                "user": _user_data(utilisateur),
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  RESEND OTP
# ──────────────────────────────────────────────
class ResendOTP(APIView):
    """
    POST /api/auth/resend-otp/
    Body: { "email": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']

        try:
            utilisateur = Utilisateur.objects.get(email=email)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": "Utilisateur introuvable."},
                status=status.HTTP_404_NOT_FOUND
            )

        if utilisateur.active:
            return Response(
                {"error": "Compte déjà activé. Connectez-vous via /api/auth/login/."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not utilisateur.password:
            return Response(
                {
                    "error": "Vous devez d'abord créer votre mot de passe.",
                    "next_step": "activation",
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        code = _generer_otp(utilisateur)
        _envoyer_otp_email(utilisateur.email, code)

        return Response(
            {
                "message": "Nouveau code OTP envoyé.",
                "email": utilisateur.email,
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  LOGIN (connexions suivantes)
# ──────────────────────────────────────────────
class Login(APIView):
    """
    POST /api/auth/login/
    Body: { "identifiant": "matricule ou email", "password": "..." }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        identifiant = data['identifiant'].strip()
        password    = data['password']

        # Cherche par matricule ou email
        utilisateur = None
        try:
            if '@' in identifiant:
                utilisateur = Utilisateur.objects.get(email=identifiant)
            else:
                utilisateur = Utilisateur.objects.get(matricule=identifiant)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": "Identifiants incorrects."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Vérifie le mot de passe
        if not utilisateur.check_password(password):
            return Response(
                {"error": "Identifiants incorrects."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Vérifie que le compte est activé
        if not utilisateur.active:
            return Response(
                {
                    "error": "Compte non activé. Vérifiez votre email pour le code OTP.",
                    "email": utilisateur.email,
                    "next_step": "verify_otp",
                },
                status=status.HTTP_403_FORBIDDEN
            )

        tokens = _generer_tokens(utilisateur)

        return Response(
            {
                "message": "Connexion réussie.",
                **tokens,
                "user": _user_data(utilisateur),
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  PROFIL
# ──────────────────────────────────────────────
class UserProfile(APIView):
    """
    GET /api/auth/profile/
    Header: Authorization: Bearer <access_token>
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
#  CRÉER UN ADMIN
# ──────────────────────────────────────────────
class CreateAdmin(APIView):
    """
    POST /api/auth/create-admin/
    Réservé aux admins existants (is_staff=True).
    Body: { "matricule", "email", "nom", "prenom" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Accès refusé. Réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CreateAdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        admin = Utilisateur.objects.create_user(
            matricule=data['matricule'],
            email=data['email'],
            nom=data['nom'],
            prenom=data.get('prenom', ''),
            role='admin',
        )
        admin.is_staff     = True
        admin.active       = True
        admin.save()

        send_mail(
            subject="Votre compte administrateur IUT a été créé",
            message=(
                f"Bonjour {admin.nom},\n\n"
                f"Votre compte administrateur a été créé.\n"
                f"Matricule : {admin.matricule}\n"
                f"Email : {admin.email}\n\n"
                f"Connectez-vous sur la plateforme IUT pour définir votre mot de passe."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            fail_silently=True,
        )

        return Response(
            {
                "message": "Administrateur créé avec succès.",
                "admin": {
                    "matricule": admin.matricule,
                    "email":     admin.email,
                    "nom":       admin.nom,
                    "prenom":    admin.prenom,
                },
            },
            status=status.HTTP_201_CREATED
        )


# ──────────────────────────────────────────────
#  IMPORT CSV / XML
# ──────────────────────────────────────────────
class ImportUsers(APIView):
    """
    POST /api/auth/import-users/
    Réservé aux admins.
    Form-data:
      - file : fichier CSV ou XML
      - role : 'etudiant' ou 'professeur'
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Accès refusé. Réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )

        fichier = request.FILES.get('file')
        role    = request.data.get('role', '').strip().lower()

        if not fichier:
            return Response({"error": "Aucun fichier fourni."}, status=400)

        if role not in ['etudiant', 'professeur']:
            return Response(
                {"error": "Rôle invalide. Choisissez 'etudiant' ou 'professeur'."},
                status=400
            )

        nom_fichier = fichier.name.lower()

        try:
            if nom_fichier.endswith('.csv'):
                rows = self._lire_csv(fichier)
            elif nom_fichier.endswith('.xml'):
                rows = self._lire_xml(fichier)
            else:
                return Response(
                    {"error": "Format non supporté. Utilisez CSV ou XML."},
                    status=400
                )
        except Exception as e:
            return Response({"error": f"Erreur lecture fichier : {str(e)}"}, status=400)

        return self._importer(rows, role)

    # ── Lecture CSV ────────────────────────────
    def _lire_csv(self, fichier):
        contenu = fichier.read().decode('utf-8-sig')  # gère le BOM Excel
        reader  = csv.DictReader(StringIO(contenu))
        return list(reader)

    # ── Lecture XML → conversion en liste de dicts ──
    def _lire_xml(self, fichier):
        """
        Format XML attendu (flexible) :
        <utilisateurs>
            <utilisateur>
                <matricule>ETU001</matricule>
                <email>alice@iut.cm</email>
                <nom>Alice</nom>
                ...
            </utilisateur>
        </utilisateurs>
        """
        contenu = fichier.read()
        root    = ET.fromstring(contenu)

        rows = []
        # Cherche les éléments enfants (peu importe le tag exact)
        for enfant in root:
            row = {}
            for champ in enfant:
                row[champ.tag.lower()] = (champ.text or '').strip()
            if row:
                rows.append(row)
        return rows

    # ── Import en BD ───────────────────────────
    def _importer(self, rows, role):
        created = 0
        skipped = 0
        errors  = []

        for idx, row in enumerate(rows, start=1):
            matricule = (row.get('matricule') or '').strip()
            email     = (row.get('email') or '').strip()

            if not matricule or not email:
                errors.append(f"Ligne {idx} : matricule et email requis.")
                skipped += 1
                continue

            if Utilisateur.objects.filter(matricule=matricule).exists():
                skipped += 1
                continue

            try:
                if role == 'etudiant':
                    Utilisateur.objects.create_user(
                        matricule=matricule,
                        email=email,
                        nom=row.get('nom', '').strip(),
                        prenom=row.get('prenom', '').strip(),
                        filiere=row.get('filiere', '').strip() or None,
                        niveau=row.get('niveau', '').strip() or None,
                        role='etudiant',
                    )
                else:
                    # Pour les profs : nom_complet ou nom
                    nom = (
                        row.get('nom_complet') or
                        row.get('nom') or ''
                    ).strip()
                    Utilisateur.objects.create_user(
                        matricule=matricule,
                        email=email,
                        nom=nom,
                        prenom=row.get('prenom', '').strip() or None,
                        departement=row.get('departement', '').strip() or None,
                        specialite=row.get('specialite', '').strip() or None,
                        role='professeur',
                    )
                created += 1

            except Exception as e:
                errors.append(f"Ligne {idx} ({matricule}) : {str(e)}")
                skipped += 1

        return Response(
            {
                "message":  "Import terminé.",
                "created":  created,
                "skipped":  skipped,
                "errors":   errors if errors else None,
            },
            status=status.HTTP_201_CREATED
        )


# ──────────────────────────────────────────────
#  LOGOUT
# ──────────────────────────────────────────────

class Logout(APIView):
    """
    POST /api/auth/logout/
    Header: Authorization: Bearer <access_token>
    Body: { "refresh": "<refresh_token>" }

    Blackliste le refresh token → il ne peut plus générer de nouveaux access tokens.
    L'access token actuel reste valide jusqu'à son expiration (1h max).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {"error": "Le refresh token est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"error": "Token invalide ou déjà révoqué."},
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {"message": "Déconnexion réussie."},
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  PROMOUVOIR UN PROFESSEUR EN ADMIN
# ──────────────────────────────────────────────

class PromoteToAdmin(APIView):
    """
    POST /api/auth/promote-to-admin/
    Réservé à l'admin principal (is_superuser=True).
    Body: { "matricule": "PROF001" }

    Promeut un professeur existant en admin (is_staff=True).
    Seul le superadmin peut faire ça — un admin secondaire ne peut pas
    promouvoir quelqu'un d'autre.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Seul le superadmin peut promouvoir
        if not request.user.is_superuser:
            return Response(
                {"error": "Accès refusé. Seul l'administrateur principal peut promouvoir un utilisateur."},
                status=status.HTTP_403_FORBIDDEN
            )

        matricule = request.data.get('matricule', '').strip()

        if not matricule:
            return Response(
                {"error": "Le matricule du professeur est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Cherche l'utilisateur
        try:
            utilisateur = Utilisateur.objects.get(matricule=matricule)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec le matricule {matricule}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Vérifications
        if utilisateur.is_superuser:
            return Response(
                {"error": "Cet utilisateur est déjà administrateur principal."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if utilisateur.is_staff:
            return Response(
                {"error": f"{utilisateur.nom} est déjà administrateur."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if utilisateur.role != 'professeur':
            return Response(
                {"error": "Seul un professeur peut être promu administrateur."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Promotion
        utilisateur.is_staff = True
        utilisateur.role     = 'admin'
        utilisateur.save()

        # Notifier le professeur promu par email
        send_mail(
            subject="Vous avez été promu administrateur — IUT",
            message=(
                f"Bonjour {utilisateur.nom},\n\n"
                f"Votre compte a été promu au rôle d'administrateur "
                f"par {request.user.nom} {request.user.prenom}.\n\n"
                f"Vous avez maintenant accès à toutes les fonctionnalités d'administration.\n\n"
                f"Connectez-vous sur la plateforme IUT."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=True,
        )

        return Response(
            {
                "message": f"{utilisateur.nom} {utilisateur.prenom} a été promu administrateur avec succès.",
                "utilisateur": {
                    "matricule": utilisateur.matricule,
                    "email":     utilisateur.email,
                    "nom":       utilisateur.nom,
                    "prenom":    utilisateur.prenom,
                    "role":      utilisateur.role,
                    "is_staff":  utilisateur.is_staff,
                },
            },
            status=status.HTTP_200_OK
            
        )

# ──────────────────────────────────────────────
#  RECHERCHE UTILISATEURS
# ──────────────────────────────────────────────
class SearchUsers(APIView):
    """
    GET /api/auth/search-users/?q=...
    Recherche par matricule, nom, prénom ou email.
    Réservé aux admins.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_staff:
            return Response(
                {"error": "Accès refusé. Réservé aux administrateurs."},
                status=status.HTTP_403_FORBIDDEN
            )

        q = request.query_params.get('q', '').strip()

        if not q:
            return Response(
                {"error": "Paramètre de recherche requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        utilisateurs = Utilisateur.objects.filter(
            Q(matricule__icontains=q) |
            Q(nom__icontains=q)       |
            Q(prenom__icontains=q)    |
            Q(email__icontains=q)
        ).exclude(matricule=request.user.matricule)

        data = [
            {
                "matricule":  u.matricule,
                "email":      u.email,
                "nom":        u.nom,
                "prenom":     u.prenom,
                "role":       u.role,
                "is_staff":   u.is_staff,
                "active":     u.active,
            }
            for u in utilisateurs
        ]

        return Response({"results": data, "count": len(data)}, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────
#  RETIRER DROITS ADMIN
# ──────────────────────────────────────────────
class DemoteAdmin(APIView):
    """
    POST /api/auth/demote-admin/
    Retire les droits admin d'un professeur promu.
    Seul le superadmin peut faire ça.
    Body: { "matricule": "PROF001" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Accès refusé. Seul l'administrateur principal peut retirer les droits admin."},
                status=status.HTTP_403_FORBIDDEN
            )

        matricule = request.data.get('matricule', '').strip()

        if not matricule:
            return Response(
                {"error": "Le matricule est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            utilisateur = Utilisateur.objects.get(matricule=matricule)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec le matricule {matricule}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Vérifications
        if utilisateur.is_superuser:
            return Response(
                {"error": "Impossible de retirer les droits au superadmin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not utilisateur.is_staff:
            return Response(
                {"error": f"{utilisateur.nom} n'est pas administrateur."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retrait des droits
        utilisateur.is_staff = False
        utilisateur.role     = 'professeur'
        utilisateur.save()

        # Notifier l'utilisateur
        send_mail(
            subject="Modification de vos droits — IUT",
            message=(
                f"Bonjour {utilisateur.nom},\n\n"
                f"Vos droits d'administrateur ont été retirés par "
                f"{request.user.nom} {request.user.prenom}.\n\n"
                f"Vous redevenez professeur sur la plateforme IUT."
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[utilisateur.email],
            fail_silently=True,
        )

        return Response(
            {
                "message": f"Les droits admin de {utilisateur.nom} {utilisateur.prenom} ont été retirés.",
                "utilisateur": {
                    "matricule": utilisateur.matricule,
                    "email":     utilisateur.email,
                    "nom":       utilisateur.nom,
                    "prenom":    utilisateur.prenom,
                    "role":      utilisateur.role,
                    "is_staff":  utilisateur.is_staff,
                },
            },
            status=status.HTTP_200_OK
        )


# ──────────────────────────────────────────────
#  DÉSACTIVER UN COMPTE
# ──────────────────────────────────────────────
class DeactivateUser(APIView):
    """
    POST /api/auth/deactivate-user/
    Désactive un compte (active=False) sans le supprimer.
    Seul le superadmin peut faire ça.
    Body: { "matricule": "ETU001" }
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_superuser:
            return Response(
                {"error": "Accès refusé. Seul l'administrateur principal peut désactiver un compte."},
                status=status.HTTP_403_FORBIDDEN
            )

        matricule = request.data.get('matricule', '').strip()

        if not matricule:
            return Response(
                {"error": "Le matricule est requis."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            utilisateur = Utilisateur.objects.get(matricule=matricule)
        except Utilisateur.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec le matricule {matricule}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Vérifications
        if utilisateur.is_superuser:
            return Response(
                {"error": "Impossible de désactiver le superadmin."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not utilisateur.active:
            return Response(
                {"error": f"Le compte de {utilisateur.nom} est déjà désactivé."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Désactivation
        utilisateur.active = False
        utilisateur.save()

        return Response(
            {
                "message": f"Le compte de {utilisateur.nom} {utilisateur.prenom} a été désactivé.",
                "utilisateur": {
                    "matricule": utilisateur.matricule,
                    "email":     utilisateur.email,
                    "nom":       utilisateur.nom,
                    "prenom":    utilisateur.prenom,
                    "role":      utilisateur.role,
                    "active":    utilisateur.active,
                },
            },
            status=status.HTTP_200_OK
        )