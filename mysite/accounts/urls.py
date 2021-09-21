from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name="index"),
    path('login/', views.MyLoginView.as_view(), name="login"),
    path('logout/', views.MyLogoutView.as_view(), name="logout"),
    path('create/', views.UserCreateView.as_view(), name="create"),
]
