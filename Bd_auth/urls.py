from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    Activation,
    # SetPassword,
    VerifyOTP,
    ResendOTP,
    Login,
    Logout,
    UserProfile,
    CreateAdmin,
    ImportUsers,
    PromoteToAdmin,
    SearchUsers,
    DeactivateUser,
    DemoteAdmin,
    EnregistrerTokenFCM,
    
)

urlpatterns = [
    # ── Flux d'activation (première connexion) ──────────────
    path('activation/',    Activation.as_view(),  name='auth-activation'),
    # path('set-password/',  SetPassword.as_view(), name='auth-set-password'),
    path('verify-otp/',    VerifyOTP.as_view(),   name='auth-verify-otp'),
    path('resend-otp/',    ResendOTP.as_view(),   name='auth-resend-otp'),

    # ── Connexion (comptes déjà activés) ────────────────────
    path('login/',         Login.as_view(),       name='auth-login'),
    path('logout/',        Logout.as_view(),      name='auth-logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # ── Profil ──────────────────────────────────────────────
    path('profile/',       UserProfile.as_view(), name='auth-profile'),

    # ── Admin ───────────────────────────────────────────────
    path('create-admin/',      CreateAdmin.as_view(),    name='auth-create-admin'),
    path('promote-to-admin/',  PromoteToAdmin.as_view(), name='auth-promote-admin'),
    path('search-users/', SearchUsers.as_view(), name='search-users'),
    path('deactivate-user/', DeactivateUser.as_view(), name='deactivate-user'),
    path('demote-admin/', DemoteAdmin.as_view(), name='demote-admin'),
    path('import-users/',      ImportUsers.as_view(),    name='auth-import-users'),
    path('token-fcm/', EnregistrerTokenFCM.as_view(), name='token-fcm'),]