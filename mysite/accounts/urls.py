from django.urls import path, include
from . import views
from django.urls import reverse_lazy
from .models import User

app_name = 'accounts'
user = User
urlpatterns = [
    path('login/', views.MyLoginView.as_view(), name="login"),
    path('logout/', views.MyLogoutView.as_view(), name="logout"),
    path('create/', views.UserCreateView.as_view(), name="create"),
    path('edit/', views.UserChangeView.as_view(), name="edit"),
    path('icon/', views.edit_profile_icon, name="icon"),
    path('password/', views.UserPasswordChangeView.as_view(), name="password"),
    path('@<str:username>/', views.user_profile, name='profile'),
    path('remove/@<str:username>/', views.remove, name="remove"),
    path('follow/@<str:username>/', views.follow, name="follow"),
]
