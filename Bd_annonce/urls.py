from django.urls import path
from .views import AnnonceList, AnnonceDetail, Marquer_lu
from rest_framework.permissions import IsAuthenticated

urlpatterns = [
    path("annonces/", AnnonceList.as_view(), name="annonces-list"),
    path('announcements/<int:pk>/', AnnonceDetail.as_view(), name="announcements-detail"),
    path('announcements/<int:pk>/read/', Marquer_lu.as_view(), name="announcements-read"),
]
