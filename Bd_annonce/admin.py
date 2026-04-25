from django.contrib import admin
from .models import Annonce, PieceJointe


class PieceJointeInline(admin.TabularInline):
    model = PieceJointe
    extra = 1


@admin.register(Annonce)
class AnnonceAdmin(admin.ModelAdmin):
    list_display = ("titre", "role_cible", "date_publication", "auteur")
    list_filter = ("role_cible", "date_publication")
    search_fields = ("titre", "contenu")
    inlines = [PieceJointeInline]


@admin.register(PieceJointe)
class PieceJointeAdmin(admin.ModelAdmin):
    list_display = ("annonce", "fichier")


