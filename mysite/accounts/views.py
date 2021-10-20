from django.contrib import messages
# Create your views here.
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView
from django.views.generic import TemplateView, CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render, redirect

from . import forms
from post.models import Post, Like
from .forms import UpLoadProfileImgForm


class MyLoginView(LoginView):
    form_class = forms.LoginForm
    template_name = "accounts/login.html"

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'ログインしました。')
        return result


class MyLogoutView(LoginRequiredMixin, LogoutView):
    template_name = "accounts/logout.html"


class IndexView(TemplateView):
    template_name = "accounts/index.html"


class UserCreateView(CreateView):
    form_class = forms.CustomUserCreationForm
    template_name = "accounts/create.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'アカウントを作成しました。')
        return result


class UserChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/edit.html'
    form_class = forms.UserChangeForm

    def form_valid(self, form):
        # formのupdateメソッドにログインユーザーを渡して更新
        form.update(user=self.request.user)
        result = super().form_valid(form)
        messages.success(self.request, 'ユーザー情報を変更しました。')
        return result

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 更新前のユーザー情報をkwargsとして渡す
        kwargs.update({
            'username': self.request.user.username,
            'email': self.request.user.email,
            'introduction': self.request.user.introduction,
        })
        return kwargs

    def get_success_url(self):
        return reverse_lazy('accounts:profile', args=[self.request.user.username])


class UserPasswordChangeView(PasswordChangeView):
    def get_success_url(self):
        return reverse_lazy('accounts:profile', args=[self.request.user.username])

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'パスワードを変更しました。')
        return result


def user_profile_view(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    me = request.user
    followers = user.followers.all()
    is_following = request.user in followers
    follower_count = followers.count()
    followings = user.following.all()
    following_count = followings.count()
    postlist = Post.objects.filter(
        author__username=username).order_by('-created_at')
    liked_set = set()
    liked_count = [None] * len(postlist)
    for i, post in enumerate(postlist):
        if post.like_set.filter(user=me).exists():
            liked_set.add(post.pk)
        liked_count[i] = Like.objects.filter(post=post).count()
    context = {
        'User': user,
        'post_list': postlist,
        'liked_set': liked_set,
        'liked_count': liked_count,
        'is_following': is_following,
        'followers': followers,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    if request.method == 'POST':
        pass
    return render(request, 'accounts/user_profile.html', context)


def remove_view(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user.followers.remove(request.user)
    user.save()
    messages.warning(request, 'リムーブしました。')
    return redirect(request.META['HTTP_REFERER'])


def follow_view(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user.followers.add(request.user)
    user.save()
    messages.success(request, 'フォローしました。')
    return redirect(request.META['HTTP_REFERER'])


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
            messages.success(request, 'アイコンを変更しました。')
            return redirect('accounts:profile', user.username)
    context = {
        'form': form
    }
    return render(request, 'accounts/icon.html', context)


class AccountsListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/account_list.html'
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        context['description'] = "ユーザー一覧"
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        qs = get_user_model().objects.all()
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs


class FollowingListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/account_list.html'
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        context['description'] = "@" + \
            self.kwargs.get('username', "") + "さんのフォロー一覧"
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        username = self.kwargs.get('username')
        qs = get_object_or_404(
            get_user_model(), username=username).following.all()
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs


class FollowerListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/account_list.html'
    model = get_user_model()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        context['description'] = "@" + \
            self.kwargs.get('username', "") + "さんのフォロワー一覧"
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        username = self.kwargs.get('username', "")
        qs = get_object_or_404(
            get_user_model(), username=username).followers.all()
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs
