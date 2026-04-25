from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.

class Role(models.Model):
    role =models.CharField(max_length=30, unique=True)
    
    def __str__(self):
        return self.role
class Filiere(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom
   
class Niveau(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nom
    
class Utilisateur(models.Model):
    matricule = models.CharField(max_length=30, unique= True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    email = models.EmailField(null=True, blank=True)
    mot_de_passe = models.CharField(max_length=255, blank=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL ,null=True, blank=True)
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True)
    role= models.ForeignKey(Role, on_delete=models.PROTECT)
    active= models.BooleanField(default= False) #faux par defaut pour nou permettre de savoir si le compte d'un utilisateu r est active ou non 
    date_creation= models.DateTimeField(auto_now_add= True)
    
    def set_password(self, raw_password):
        self.mot_de_passe = make_password(raw_password)
        
    def check_password(self, raw_password):
        return check_password(raw_password,  self.mot_de_passe)
    
    def __str__(self):
        return  f"{self.nom}, {self.prenom}, {self.matricule} {self.filiere} {self.niveau}"   

class OTP(models.Model):
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_valid = models.BooleanField(default=True)  

   
   

    
    # def __str__(self):
        # return f"{self.role} - {self.matricule} - {self.prenom} {self.nom} - {self.filiere} - {self.niveau}"
 