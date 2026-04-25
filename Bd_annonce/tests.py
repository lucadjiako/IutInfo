from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Annonce, Lecture
from Bd_auth.models import Utilisateur, Role, Filiere, Niveau


class AnnonceSetupMixin:
    """Mixin pour créer des données de test pour les annonces"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Créer les rôles, filières et niveaux
        self.role_etudiant = Role.objects.create(role="Etudiant")
        self.role_admin = Role.objects.create(role="Admin")
        self.filiere = Filiere.objects.create(nom="Informatique")
        self.niveau = Niveau.objects.create(nom="L2")
        
        # Créer un utilisateur auteur d'annonces
        self.author = Utilisateur.objects.create(
            matricule="MT001",
            nom="Dupont",
            prenom="Jean",
            email="author@example.com",
            filiere=self.filiere,
            niveau=self.niveau,
            role=self.role_admin,
            active=True
        )
        
        # Créer un utilisateur étudiant
        self.student = Utilisateur.objects.create(
            matricule="MT002",
            nom="Martin",
            prenom="Marie",
            email="student@example.com",
            filiere=self.filiere,
            niveau=self.niveau,
            role=self.role_etudiant,
            active=True
        )
        
        # Créer un utilisateur sans authentification
        self.unauthenticated_client = APIClient()
        
        # Obtenir les tokens pour les utilisateurs
        self.author_token = self._get_token(self.author)
        self.student_token = self._get_token(self.student)
        
        # Créer une annonce
        self.annonce = Annonce.objects.create(
            titre="Annonce Test",
            contenu="Contenu de l'annonce test",
            auteur=self.author,
            filiere=self.filiere,
            niveau=self.niveau,
            role_cible=self.role_etudiant
        )
    
    def _get_token(self, user):
        """Obtenir un token JWT pour un utilisateur"""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def _authenticate_client(self, user_token):
        """Authentifier le client avec un token"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {user_token}')


class AnnonceListTestCase(AnnonceSetupMixin, APITestCase):
    """Tests pour la liste des annonces"""
    
    def test_list_annonces_authentifie(self):
        """Test la récupération de la liste des annonces par un utilisateur authentifié"""
        self._authenticate_client(self.student_token)
        response = self.client.get(reverse('annonces-list'))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)
    
    def test_list_annonces_non_authentifie(self):
        """Test que l'accès est refusé sans authentification"""
        response = self.unauthenticated_client.get(reverse('annonces-list'))
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AnnonceDetailTestCase(AnnonceSetupMixin, APITestCase):
    """Tests pour les détails d'une annonce"""
    
    def test_get_annonce_detail_succes(self):
        """Test la récupération des détails d'une annonce"""
        self._authenticate_client(self.student_token)
        response = self.client.get(reverse('announcements-detail', args=[self.annonce.pk]))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titre'], "Annonce Test")
        self.assertEqual(response.data['contenu'], "Contenu de l'annonce test")
    
    def test_get_annonce_inexistante(self):
        """Test la récupération d'une annonce inexistante"""
        self._authenticate_client(self.student_token)
        response = self.client.get(reverse('announcements-detail', args=[9999]))
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_update_annonce_par_auteur(self):
        """Test la modification d'une annonce par son auteur"""
        self._authenticate_client(self.author_token)
        
        data = {
            "titre": "Annonce Modifiée",
            "contenu": "Contenu modifié"
        }
        response = self.client.put(
            reverse('announcements-detail', args=[self.annonce.pk]),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['titre'], "Annonce Modifiée")
        
        # Vérifier que l'annonce est bien modifiée en BD
        self.annonce.refresh_from_db()
        self.assertEqual(self.annonce.titre, "Annonce Modifiée")
    
    def test_update_annonce_par_non_auteur(self):
        """Test que la modification est refusée pour non-auteur"""
        self._authenticate_client(self.student_token)
        
        data = {
            "titre": "Tentative de modification",
            "contenu": "Ceci ne devrait pas fonctionner"
        }
        response = self.client.put(
            reverse('announcements-detail', args=[self.annonce.pk]),
            data,
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "Non autorisé")
    
    def test_delete_annonce_par_auteur(self):
        """Test la suppression d'une annonce par son auteur"""
        self._authenticate_client(self.author_token)
        
        response = self.client.delete(
            reverse('announcements-detail', args=[self.annonce.pk])
        )
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Vérifier que l'annonce est bien supprimée
        self.assertFalse(Annonce.objects.filter(pk=self.annonce.pk).exists())
    
    def test_delete_annonce_par_non_auteur(self):
        """Test que la suppression est refusée pour non-auteur"""
        self._authenticate_client(self.student_token)
        
        response = self.client.delete(
            reverse('announcements-detail', args=[self.annonce.pk])
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "Non autorisé")


class MarquerLuTestCase(AnnonceSetupMixin, APITestCase):
    """Tests pour marquer une annonce comme lue"""
    
    def test_marquer_lu_succes(self):
        """Test le marquage d'une annonce comme lue"""
        self._authenticate_client(self.student_token)
        
        response = self.client.post(
            reverse('announcements-read', args=[self.annonce.pk])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Annonce marquée comme lue")
        
        # Vérifier que la lecture est enregistrée
        self.assertTrue(Lecture.objects.filter(
            utilisateur=self.student,
            annonce=self.annonce
        ).exists())
    
    def test_marquer_lu_double_appel(self):
        """Test que marquer deux fois ne crée qu'une seule entrée"""
        self._authenticate_client(self.student_token)
        
        # Premier appel
        self.client.post(reverse('announcements-read', args=[self.annonce.pk]))
        
        # Deuxième appel (ne doit pas créer d'erreur)
        response = self.client.post(
            reverse('announcements-read', args=[self.annonce.pk])
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier qu'une seule entrée existe
        count = Lecture.objects.filter(
            utilisateur=self.student,
            annonce=self.annonce
        ).count()
        self.assertEqual(count, 1)
    
    def test_marquer_lu_non_authentifie(self):
        """Test que l'accès est refusé sans authentification"""
        response = self.unauthenticated_client.post(
            reverse('announcements-read', args=[self.annonce.pk])
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
