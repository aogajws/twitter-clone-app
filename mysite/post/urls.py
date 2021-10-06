from django.urls import path
from . import views


app_name = 'post'
urlpatterns = [
    path('', views.PostListView.as_view(), name='post_list'),
    path('post_create/', views.PostCreateView.as_view(), name='post_create'),
    path('search/', views.SearchPostListView.as_view(), name='search'),
    path('replies/', views.ReplyPostListView.as_view(), name='replies'),
    path('status/<int:pk>/', views.PostStatus.as_view(), name='status'),
    path('reply/<int:pk>/', views.reply_create_view, name='reply'),
    path('favorite/<int:pk>/', views.favorite_view, name='favorite'),
    path('delete/<int:pk>/', views.delete_view, name='delete'),
]
