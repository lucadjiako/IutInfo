from django.urls import path
from .views import AnnonceList, AnnonceDetail, MarquerLu, AnnonceStats

urlpatterns = [
    path('',              AnnonceList.as_view(),   name='annonce-list'),
    path('<int:pk>/',     AnnonceDetail.as_view(),  name='annonce-detail'),
    path('<int:pk>/lu/',  MarquerLu.as_view(),      name='annonce-lu'),
    path('<int:pk>/stats/', AnnonceStats.as_view(), name='annonce-stats'),
]