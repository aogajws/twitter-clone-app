from django.urls import path, include
from . import views

app_name = 'accounts'
urlpatterns = [
    # path('', views.IndexView.as_view(), name="index"),
    path('login/', views.MyLoginView.as_view(), name="login"),
    path('logout/', views.MyLogoutView.as_view(), name="logout"),
    path('create/', views.UserCreateView.as_view(), name="create"),
    path('@<str:username>/remove/', views.remove_view, name="remove"),
    path('@<str:username>/follow/', views.follow_view, name="follow"),
    path('@<str:username>/', views.user_profile_view, name='profile'),
]
