from .forms import UpLoadProfileImgForm
from .models import User
from django.shortcuts import render, redirect

# Create your views here.
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
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


class UserChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/edit.html'
    form_class = forms.UserChangeForm
    success_url = reverse_lazy('post:post_list')

    def form_valid(self, form):
        # formのupdateメソッドにログインユーザーを渡して更新
        form.update(user=self.request.user)
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 更新前のユーザー情報をkwargsとして渡す
        kwargs.update({
            'username': self.request.user.username,
            'email': self.request.user.email,
        })
        return kwargs


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


def edit_profile_icon(request):
    if request.method != 'POST':
        form = UpLoadProfileImgForm()
    else:
        form = UpLoadProfileImgForm(request.POST, request.FILES)
        if form.is_valid():
            icon = form.cleaned_data['icon']
            user = request.user
            user.icon = icon
            user.save()
            return redirect('accounts:profile', user.username)
    context = {
        'form': form
    }
    return render(request, 'accounts/icon.html', context)
