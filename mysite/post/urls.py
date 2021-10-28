from django.urls import path, include
from . import views


app_name = 'post'
urlpatterns = [
    path('post_create/', views.PostCreateView.as_view(), name='post_create'),
    path('search/', views.SearchPostListView.as_view(), name='search'),
    path('<int:pk>/favorite/', views.favorite_view, name='favorite'),
    path('<int:pk>/delete/', views.delete_view, name='delete'),
    path('', views.PostListView.as_view(), name='post_list'),
]
