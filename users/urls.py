from django.urls import path

from .views import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    ProfileView,
    RequestPasswordResetView,
    ResetPasswordView,
    SignupView,
)

urlpatterns = [
    path('login/', LoginView.as_view()),
    path('signup/', SignupView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('profile/', ProfileView.as_view()),
    path('change-password/', ChangePasswordView.as_view()),
    path('request-password-reset/', RequestPasswordResetView.as_view()),
    path('reset-password/', ResetPasswordView.as_view()),
]
