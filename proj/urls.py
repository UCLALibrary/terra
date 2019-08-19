"""proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib.auth import views as auth_views
from terra.views import EmployeeDetailView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='terra/registration/login.html')),
    path('logout/', auth_views.LogoutView.as_view(template_name='terra/registration/logout.html')),
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='terra/registration/password_change.html')),
    path('password_change_done/', auth_views.PasswordChangeDoneView.as_view(template_name='terra/registration/password_change_done.html')),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='terra/registration/password_reset.html')),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(template_name='terra/registration/password_reset_done.html')),
    path('password_reset_confirm/', auth_views.PasswordResetConfirmView.as_view(template_name='terra/registration/password_reset_confirm.html')),
    path('password_reset_complete/', auth_views.PasswordResetCompleteView.as_view(template_name='terra/registration/password_reset_complete.html')),
    
]
