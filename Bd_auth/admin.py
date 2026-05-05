from django.contrib import admin
from .models import Utilisateur, OTP

# Register your models here.

admin.site.register(Utilisateur)
admin.site.register(OTP)
