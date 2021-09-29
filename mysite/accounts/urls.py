from django.urls import path, include
from . import views
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy

app_name = 'accounts'
urlpatterns = [
    path('login/', views.MyLoginView.as_view(), name="login"),
    path('logout/', views.MyLogoutView.as_view(), name="logout"),
    path('create/', views.UserCreateView.as_view(), name="create"),
    path('edit/', views.UserChangeView.as_view(), name="edit"),
    path('icon/', views.edit_profile_icon, name="icon"),
    path('password/', auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy('accounts:profile')), name="password"),
    path('@<str:username>/', views.user_profile, name='profile'),
    path('remove/@<str:username>/', views.remove, name="remove"),
    path('follow/@<str:username>/', views.follow, name="follow"),
]
