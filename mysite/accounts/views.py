from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from . import forms
from post.models import Post
from django.views.generic import TemplateView, CreateView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model


class MyLoginView(LoginView):
    form_class = forms.LoginForm
    template_name = "accounts/login.html"


class MyLogoutView(LoginRequiredMixin, LogoutView):
    template_name = "accounts/logout.html"


class IndexView(TemplateView):
    template_name = "accounts/index.html"


class UserCreateView(CreateView):
    form_class = forms.CustomUserCreationForm
    template_name = "accounts/create.html"
    success_url = reverse_lazy("accounts:login")


def user_profile(request, username):
    user = get_user_model().objects.get(username=username)
    followers = user.followers.all()
    is_following = request.user in followers
    follower_count = followers.count()
    followings = user.following.all()
    following_count = followings.count()
    context = {
        'User': user,
        'post_list': Post.objects.filter(author__username=username).order_by('-created_at'),
        'is_following': is_following,
        'followers': followers,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    if request.method == 'POST':
        pass
    return render(request, 'accounts/user_profile.html', context)


def remove(request, username):
    user = get_user_model().objects.get(username=username)
    user.followers.remove(request.user)
    user.save()
    return redirect('accounts:profile', username)


def follow(request, username):
    user = get_user_model().objects.get(username=username)
    user.followers.add(request.user)
    user.save()
    return redirect('accounts:profile', username)
