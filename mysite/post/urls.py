from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'post'
urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post_create/', views.PostCreateView.as_view(), name='post_create'),
]
