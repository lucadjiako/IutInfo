from django.urls import path
from .views import ActivationCompte, Login, Verification_OTP; 
urlpatterns = [
    path('activer-compte/', ActivationCompte.as_view()),
    path('login/', Login.as_view()),
    path('verify-otp/', Verification_OTP.as_view()),
]