# Guide de Test des APIs - IutInfo

## Vue d'ensemble

Ce projet contient des tests unitaires automatisés pour valider tous les endpoints des deux applications :
- **Bd_auth** : Authentification, activation, OTP
- **Bd_annonce** : Gestion des annonces

---

## Structure des Tests

### 1. Tests d'Authentification (`Bd_auth/tests.py`)

#### **ActivationCompteTestCase**
- ✅ `test_activation_compte_succes` : Activation réussie d'un compte
- ❌ `test_activation_utilisateur_inexistant` : Essai d'activation d'un utilisateur non trouvé
- ❌ `test_activation_compte_deja_active` : Essai d'activation d'un compte déjà actif

#### **LoginTestCase**
- ✅ `test_login_succes` : Connexion réussie (génère OTP)
- ❌ `test_login_utilisateur_inexistant` : Essai avec email inexistant
- ❌ `test_login_mot_de_passe_incorrect` : Essai avec mauvais mot de passe
- ❌ `test_login_compte_non_active` : Essai avec compte inactif

#### **VerificationOTPTestCase**
- ✅ `test_verification_otp_succes` : Vérification OTP réussie
- ❌ `test_verification_otp_code_invalide` : Code OTP invalide
- ❌ `test_verification_utilisateur_inexistant` : Email inexistant

### 2. Tests d'Annonces (`Bd_annonce/tests.py`)

#### **AnnonceListTestCase**
- ✅ `test_list_annonces_authentifie` : Récupération de la liste (authentifié)
- ❌ `test_list_annonces_non_authentifie` : Accès refusé sans authentification

#### **AnnonceDetailTestCase**
- ✅ `test_get_annonce_detail_succes` : Récupération des détails
- ❌ `test_get_annonce_inexistante` : Annonce inexistante (404)
- ✅ `test_update_annonce_par_auteur` : Modification par l'auteur
- ❌ `test_update_annonce_par_non_auteur` : Modification refusée pour non-auteur
- ✅ `test_delete_annonce_par_auteur` : Suppression par l'auteur
- ❌ `test_delete_annonce_par_non_auteur` : Suppression refusée pour non-auteur

#### **MarquerLuTestCase**
- ✅ `test_marquer_lu_succes` : Marquage comme lue
- ✅ `test_marquer_lu_double_appel` : Pas de doublon au 2ème appel
- ❌ `test_marquer_lu_non_authentifie` : Accès refusé sans authentification

---

## Comment Exécuter les Tests

### 1. **Exécuter TOUS les tests**
```powershell
python manage.py test --settings=IutInfo.settings
```

### 2. **Exécuter les tests d'une application spécifique**
```powershell
# Tests d'authentification
python manage.py test Bd_auth --settings=IutInfo.settings

# Tests d'annonces
python manage.py test Bd_annonce --settings=IutInfo.settings
```

### 3. **Exécuter une classe de tests**
```powershell
# Classe LoginTestCase
python manage.py test Bd_auth.tests.LoginTestCase --settings=IutInfo.settings
```

### 4. **Exécuter un test spécifique**
```powershell
# Seul le test de succès du login
python manage.py test Bd_auth.tests.LoginTestCase.test_login_succes --settings=IutInfo.settings
```

### 5. **Tests avec verbosité (plus de détails)**
```powershell
# Niveau 2 : informations détaillées
python manage.py test --settings=IutInfo.settings -v 2

# Niveau 3 : informations très détaillées
python manage.py test --settings=IutInfo.settings -v 3
```

### 6. **Tests avec couverture (coverage)**
Installez d'abord coverage :
```powershell
pip install coverage
```

Puis executez :
```powershell
coverage run --source='.' manage.py test --settings=IutInfo.settings
coverage report
coverage html  # Génère un rapport HTML
```

---

## Résultats Attendus

Quand vous exécutez les tests, vous devez voir :

```
Creating test database for alias 'default'...
...
----------------------------------------------------------------------
Ran 19 tests in 2.345s

OK
Destroying test database for alias 'default'...
```

**Signification :**
- 🟢 `.` = Un test passé
- 🔴 `F` = Un test échoué
- 🟡 `E` = Une erreur
- `OK` = Tous les tests sont passés

---

## Comprendre les Tests

### **APITestCase vs TestCase**
- `APITestCase` : Pour les tests d'API REST (ce qu'on utilise)
- `TestCase` : Pour les tests généraux de models

### **APIClient**
C'est notre "navigateur" pour faire des requêtes HTTP :
```python
# Créer un client
client = APIClient()

# Faire une requête POST
response = client.post('/api/auth/login/', data={'email': 'test@example.com', 'password': 'pass'})

# Vérifier le statut
self.assertEqual(response.status_code, status.HTTP_200_OK)
```

### **Authentification JWT**
```python
# S'authentifier avec un token
client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

# Accéder à un endpoint protégé
response = client.get('/api/annonces/annonces/')
```

### **Setup et Teardown**
```python
def setUp(self):
    # Exécuté AVANT chaque test
    # Créer les données de test
    pass

def tearDown(self):
    # Exécuté APRÈS chaque test
    # Nettoyer (optionnel, Django le fait automatiquement)
    pass
```

---

## Troubleshooting

### ❌ Erreur : "reverse() not found"
**Cause** : La route n'a pas de nom
**Solution** : Ajouter un `name=` dans `urls.py` (déjà fait ✓)

### ❌ Erreur : "404 Not Found"
**Cause** : L'endpoint n'existe pas
**Solution** : Vérifier l'URL et les routes dans `urls.py`

### ❌ Erreur : "Assertion Failed"
**Cause** : Le test attendait une valeur différente
**Solution** : Vérifier la logique métier de votre view

### ❌ "SQLite database is locked"
**Cause** : Plusieurs tests s'exécutent sur la BD en même temps
**Solution** : Django teste en transaction et rollback, ça devrait passer. Sinon redémarrer.

---

## Exemple : Exécution Pas à Pas

### Terminal 1 - Exécuter les tests d'authentification
```powershell
PS D:\Django\IutInfo> python manage.py test Bd_auth --settings=IutInfo.settings -v 2

# Résultat :
Creating test database for alias 'default'...
Creating table django_content_type...
Creating table django_session...
Creating table Bd_auth_role...
Creating table Bd_auth_filiere...
Creating table Bd_auth_niveau...
Creating table Bd_auth_utilisateur...
Creating table Bd_auth_otp...
...

test_activation_compte_deja_active (Bd_auth.tests.ActivationCompteTestCase) ... ok
test_activation_compte_succes (Bd_auth.tests.ActivationCompteTestCase) ... ok
test_activation_utilisateur_inexistant (Bd_auth.tests.ActivationCompteTestCase) ... ok
test_login_compte_non_active (Bd_auth.tests.LoginTestCase) ... ok
test_login_mot_de_passe_incorrect (Bd_auth.tests.LoginTestCase) ... ok
test_login_succes (Bd_auth.tests.LoginTestCase) ... ok
test_login_utilisateur_inexistant (Bd_auth.tests.LoginTestCase) ... ok
test_verification_otp_code_invalide (Bd_auth.tests.VerificationOTPTestCase) ... ok
test_verification_otp_succes (Bd_auth.tests.VerificationOTPTestCase) ... ok
test_verification_utilisateur_inexistant (Bd_auth.tests.VerificationOTPTestCase) ... ok

----------------------------------------------------------------------
Ran 10 tests in 1.234s

OK
Destroying test database for alias 'default'...
```

### Vérification Manuelle (Alternative)

Si tu préfères tester manuellement avec Postman ou HTTPie :

1. **Démarrer le serveur**
   ```powershell
   python manage.py runserver --settings=IutInfo.settings
   ```

2. **Activation de compte**
   ```bash
   http POST http://localhost:8000/api/auth/activer-compte/ \
     matricule=MT001 \
     nom=Dupont \
     prenom=Jean \
     mot_de_passe=MyPassword123
   ```

3. **Login**
   ```bash
   http POST http://localhost:8000/api/auth/login/ \
     email=jean@example.com \
     password=MyPassword123
   ```

4. **Vérifier OTP**
   ```bash
   http POST http://localhost:8000/api/auth/verify-otp/ \
     email=jean@example.com \
     code=123456
   ```

---

## Prochaines Étapes

1. ✅ Tous les tests passent
2. 📊 Vérifier la couverture des tests (visez 80%+)
3. 🔄 Ajouter CI/CD (GitHub Actions) pour tester automatiquement
4. 📈 Augmenter les cas de test pour les edge cases

Bonne chance avec tes tests ! 🚀
