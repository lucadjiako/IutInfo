from django.db import models

# from django.utils import timezone
from Bd_auth.models import Utilisateur, Role, Filiere, Niveau

#creation de class annonce

class Annonce(models.Model):
    titre = models.CharField(max_length=255)
    contenu = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_publication = models.DateTimeField(auto_now_add=True)
    auteur = models.ForeignKey(Utilisateur,on_delete=models.CASCADE,related_name="annonces")
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL ,null=True, blank=True)
    niveau = models.ForeignKey(Niveau, on_delete=models.SET_NULL, null=True, blank=True)
    role_cible = models.ForeignKey(Role,on_delete=models.CASCADE, null=True, blank=True)
    

    # def est_visible(self):
    #     return self.date_publication <= timezone.now()

    def __str__(self):
        return self.titre

#attachement de la piece jointe a l'annonce 

class PieceJointe(models.Model):
    annonce = models.ForeignKey(Annonce,on_delete=models.CASCADE,related_name="pieces_jointes" )
    fichier = models.FileField(upload_to="annonces/")

    def __str__(self):
        return f"Fichier pour {self.annonce.titre}"
    


class Lecture(models.Model):
    annonce = models.ForeignKey(Annonce, on_delete=models.CASCADE, related_name="lectures")
    utilisateur = models.ForeignKey(Utilisateur, on_delete=models.CASCADE)
    Lu_à = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('annonce', 'utilisateur') #Unique_togetherm c'est pour se rassurer qu4un utilisateur ne ;entionne pqs uune publication lu 

    def __str__(self): 
        return f"{self.utilisateur} a lu {self.annonce}"
    
