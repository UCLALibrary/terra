from django.contrib import admin
from django.urls import path
from django.conf.urls import include
from django.contrib.auth import views as auth_views
from django.views.generic.base import RedirectView

from terra.views import UserDashboard, UnitDetailView, UnitListView

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "accounts/login/",
        auth_views.LoginView.as_view(template_name="terra/registration/login.html"),
    ),
    path(
        "accounts/logout/",
        auth_views.LogoutView.as_view(template_name="terra/registration/logout.html"),
    ),
    path(
        "accounts/password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="terra/registration/password_change.html"
        ),
        name="password_change",
    ),
    path(
        "accounts/password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="terra/registration/password_change_done.html"
        ),
        name="password_change_done",
    ),
    path(
        "accounts/password_reset/",
        auth_views.PasswordResetView.as_view(
            template_name="terra/registration/password_reset.html"
        ),
        name="password_reset",
    ),
    path(
        "accounts/password_reset/done/",
        auth_views.PasswordResetDoneView.as_view(
            template_name="terra/registration/password_reset_done.html"
        ),
        name="password_reset_done",
    ),
    path(
        "accounts/reset/<uidb64>/<token>/",
        auth_views.PasswordResetConfirmView.as_view(
            template_name="terra/registration/password_reset_confirm.html"
        ),
        name="password_reset_confirm",
    ),
    path(
        "accounts/password/done",
        auth_views.PasswordResetCompleteView.as_view(
            template_name="terra/registration/password_reset_complete.html"
        ),
        name="password_reset_complete",
    ),
    path(
        "dashboard/",
        UserDashboard.as_view(template_name="terra/dashboard.html"),
        name="user_dashboard",
    ),
    path(
        "unit/<int:pk>/",
        UnitDetailView.as_view(template_name="terra/unit.html"),
        name="unit_detail",
    ),
    path(
        "unit/",
        UnitListView.as_view(template_name="terra/unit_list.html"),
        name="unit_list",
    ),
    path("", RedirectView.as_view(url="/dashboard"), name="home"),
]
