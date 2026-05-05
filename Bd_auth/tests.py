from django.test import TestCase, Client
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Utilisateur, OTP
import json


class UtilisateurSetupMixin:
    """Mixin pour créer des utilisateurs de test"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Créer un utilisateur inactif (pour activation)
        self.user_inactive = Utilisateur.objects.create(
            matricule="MT001",
            nom="Dupont",
            prenom="Jean",
            email="jean@example.com",
            filiere="Informatique",
            niveau="L2",
            role="etudiant",
            active=False
        )
        
        # Créer un utilisateur actif (pour login)
        self.user_active = Utilisateur.objects.create(
            matricule="MT002",
            nom="Martin",
            prenom="Marie",
            email="marie@example.com",
            filiere="Informatique",
            niveau="L2",
            role="etudiant",
            active=True
        )
        self.user_active.set_password("password123")
        self.user_active.save()


class ActivationCompteTestCase(UtilisateurSetupMixin, APITestCase):
    """Tests pour l'activation de compte"""
    
    def test_activation_compte_succes(self):
        """Test une activation de compte réussie"""
        data = {
            "matricule": "MT001",
            "nom": "Dupont",
            "prenom": "Jean",
            "mot_de_passe": "NewPassword123"
        }
        response = self.client.post(reverse('activer-compte'), data, format='json')
        
        # Vérifier le statut
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Vérifier le contenu
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["message"], "Compte activé avec succès.")
        
        # Vérifier que l'utilisateur est bien activé
        user = Utilisateur.objects.get(matricule="MT001")
        self.assertTrue(user.active)
    
    def test_activation_utilisateur_inexistant(self):
        """Test l'activation avec un utilisateur inexistant"""
        data = {
            "matricule": "INEXISTANT",
            "nom": "Inexistant",
            "prenom": "User",
            "mot_de_passe": "password123"
        }
        response = self.client.post(reverse('activer-compte'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["message"], "Acces refusé: utilisateuer non reconnu.")
    
    def test_activation_compte_deja_active(self):
        """Test l'activation d'un compte déjà activé"""
        data = {
            "matricule": "MT002",
            "nom": "Martin",
            "prenom": "Marie",
            "mot_de_passe": "AnotherPassword"
        }
        response = self.client.post(reverse('activer-compte'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["message"], "Compte déjà activé.")


class LoginTestCase(UtilisateurSetupMixin, APITestCase):
    """Tests pour la connexion"""
    
    def test_login_succes(self):
        """Test une connexion réussie"""
        data = {
            "email": "marie@example.com",
            "password": "password123"
        }
        response = self.client.post(reverse('login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Code envoyé par email")
        
        # Vérifier qu'un OTP a été créé
        otp_count = OTP.objects.filter(utilisateur=self.user_active).count()
        self.assertEqual(otp_count, 1)
    
    def test_login_utilisateur_inexistant(self):
        """Test la connexion avec un email inexistant"""
        data = {
            "email": "inexistant@example.com",
            "password": "password123"
        }
        response = self.client.post(reverse('login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Utilisateur introuvable")
    
    def test_login_mot_de_passe_incorrect(self):
        """Test la connexion avec un mauvais mot de passe"""
        data = {
            "email": "marie@example.com",
            "password": "mauvais_mot_de_passe"
        }
        response = self.client.post(reverse('login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Mot de passe incorrect")
    
    def test_login_compte_non_active(self):
        """Test la connexion avec un compte non activé"""
        data = {
            "email": "jean@example.com",
            "password": "password123"
        }
        # Ajouter un mot de passe à l'utilisateur inactif
        self.user_inactive.set_password("password123")
        self.user_inactive.save()
        
        response = self.client.post(reverse('login'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "Compte non activé")


class VerificationOTPTestCase(UtilisateurSetupMixin, APITestCase):
    """Tests pour la vérification OTP"""
    
    def test_verification_otp_succes(self):
        """Test une vérification OTP réussie"""
        # Créer un OTP valide
        otp = OTP.objects.create(
            utilisateur=self.user_active,
            code="123456",
            is_valid=True
        )
        
        data = {
            "email": "marie@example.com",
            "code": "123456"
        }
        response = self.client.post(reverse('verify-otp'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
    
    def test_verification_otp_code_invalide(self):
        """Test avec un code OTP invalide"""
        data = {
            "email": "marie@example.com",
            "code": "INVALID"
        }
        response = self.client.post(reverse('verify-otp'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Code invalide")
    
    def test_verification_utilisateur_inexistant(self):
        """Test la vérification avec un email inexistant"""
        data = {
            "email": "inexistant@example.com",
            "code": "123456"
        }
        response = self.client.post(reverse('verify-otp'), data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Utilisateur introuvable")
