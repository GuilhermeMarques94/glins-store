from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/',        views.RegisterView.as_view(),        name='register'),
    path('login/',           views.LoginView.as_view(),           name='login'),
    path('logout/',          views.LogoutView.as_view(),          name='logout'),
    path('token/refresh/',   TokenRefreshView.as_view(),          name='token_refresh'),
    path('profile/',         views.ProfileView.as_view(),         name='profile'),
    path('change-password/', views.ChangePasswordView.as_view(),  name='change_password'),

    # ── NOVO: Reset de senha ──
    path('forgot-password/',        views.forgot_password, name='forgot_password'),
    path('reset-password/confirm/', views.reset_password,  name='reset_password'),

    # ── Admin: usuários ──
    path('users/',      views.AdminUserListView.as_view(),   name='admin_user_list'),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin_user_detail'),

    # ── Temporário ──
    path('setup-admin/',     views.create_superuser_temp,         name='setup_admin'),
]
