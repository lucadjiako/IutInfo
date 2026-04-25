from django.urls import path
from .views import ActivationCompte, Login, Verification_OTP; 
urlpatterns = [
    path('activer-compte/', ActivationCompte.as_view(), name="activer-compte"),
    path('login/', Login.as_view(), name="login"),
    path('verify-otp/', Verification_OTP.as_view(), name="verify-otp"),
]