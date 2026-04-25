from django.contrib import admin
from .models import Utilisateur, Role, Filiere, Niveau

# Register your models here.

admin.site.register(Role)
admin.site.register(Utilisateur)
admin.site.register(Filiere)
admin.site.register(Niveau)
