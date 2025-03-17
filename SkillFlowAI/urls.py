from django.urls import path

from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.forms import SetPasswordForm

from django import forms

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("register", views.register, name="register"),
    path("login", views.loginView, name="login"),
    path("logout", views.logoutView, name="logout"),
    path("api/chat", views.chatAPI, name="chatAPI"),
    path("api/chatUpload", views.chatAPIUpload, name="chatAPIUpload")
]

