from django.urls import path, include
from . import views
from django.conf import settings
from django.conf.urls.static import static


app_name = 'post'
urlpatterns = [
    path('', views.post_list, name='post_list'),
    path('post_create/', views.PostCreateView.as_view(), name='post_create'),
    path('search/', views.SearchPostListView.as_view(), name='search'),
    path('<int:pk>/favorite/', views.favorite, name='favorite'),
    path('<int:pk>/delete/', views.delete, name='delete'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
