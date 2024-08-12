from django.urls import path
from . import views

urlpatterns = [
    path('',views.accueil,name='Acceuil'),
    path('login_user/', views.loginUser, name='login'),
    path('CoachSignIn/<int:id>/', views.coachSignIn, name='coach_sign_in'),
]