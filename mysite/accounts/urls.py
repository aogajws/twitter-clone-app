from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    # path('', views.IndexView.as_view(), name="index"),
    path('login/', views.MyLoginView.as_view(), name="login"),
    path('logout/', views.MyLogoutView.as_view(), name="logout"),
    path('create/', views.UserCreateView.as_view(), name="create"),
    path('@<str:username>/', views.user_profile, name='profile'),
    path('remove/@<str:username>/', views.remove, name="remove"),
    path('follow/@<str:username>/', views.follow, name="follow"),
]
