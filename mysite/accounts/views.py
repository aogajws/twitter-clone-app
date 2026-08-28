from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.views.generic.edit import FormView
from django.views.generic import TemplateView, CreateView, ListView
from django.urls import reverse_lazy
from django.contrib.auth import get_user_model, login, authenticate
from django.db.models import Count

from . import forms
from post.models import Post
from .forms import UploadProfileImgForm
from common.utils import safe_redirect, LikedPostMixin


# ---------------------------------------------------------------------------
# 認証ビュー
# ---------------------------------------------------------------------------

class MyLoginView(LoginView):
    form_class = forms.LoginForm
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'ログインしました。')
        return result


class MyLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'accounts/logout.html'

    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        messages.warning(request, 'ログアウトしました。')
        return response


class IndexView(TemplateView):
    template_name = 'accounts/index.html'


# ---------------------------------------------------------------------------
# アカウント作成・編集
# ---------------------------------------------------------------------------

class UserCreateView(CreateView):
    form_class = forms.CustomUserCreationForm
    template_name = 'accounts/create.html'
    success_url = reverse_lazy('post:post_list')

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'アカウントを作成しました。')
        username = form.cleaned_data.get('username')
        raw_pw = form.cleaned_data.get('password1')
        user = authenticate(username=username, password=raw_pw)
        login(self.request, user)
        return result


class UserChangeView(LoginRequiredMixin, FormView):
    template_name = 'accounts/edit.html'
    form_class = forms.UserChangeForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # 更新前のユーザー情報を kwargs として渡す（UserChangeForm.__init__ が instance をセット）
        kwargs.update({
            'username': self.request.user.username,
            'email': self.request.user.email,
            'introduction': self.request.user.introduction,
        })
        return kwargs

    def form_valid(self, form):
        form.update(user=self.request.user)
        result = super().form_valid(form)
        messages.success(self.request, 'ユーザー情報を変更しました。')
        return result

    def get_success_url(self):
        return reverse_lazy('accounts:profile', args=[self.request.user.username])


class UserPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    form_class = forms.UserPasswordChangeForm
    template_name = 'accounts/password_change.html'

    def get_success_url(self):
        return reverse_lazy('accounts:profile', args=[self.request.user.username])

    def form_valid(self, form):
        result = super().form_valid(form)
        messages.success(self.request, 'パスワードを変更しました。')
        return result


# ---------------------------------------------------------------------------
# プロフィール
# ---------------------------------------------------------------------------

def user_profile_view(request, username):
    profile_user = get_object_or_404(get_user_model(), username=username)
    me = request.user
    followers = profile_user.followers.all()
    is_following = me.is_authenticated and (me in followers)
    follower_count = followers.count()
    following_count = profile_user.following.count()

    post_list = (
        Post.objects
        .filter(author__username=username)
        .select_related('author', 'repost_parent__author')
        .prefetch_related('liked_users', 'replies', 'reposted')
        .annotate(
            liked_count=Count('liked_users'),
            reply_count=Count('replies'),
            repost_count=Count('reposted'),
        )
    )

    # いいね済み投稿IDをまとめて取得（N+1 クエリを回避）
    if me.is_authenticated:
        liked_post_ids = set(me.favorite_posts.values_list('pk', flat=True))
        liked = [post.pk in liked_post_ids for post in post_list]
    else:
        liked = [False] * len(post_list)

    context = {
        'User': profile_user,
        'zip': zip(post_list, liked),
        'is_following': is_following,
        'followers': followers,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    return render(request, 'accounts/user_profile.html', context)


@login_required
@require_POST
def remove_view(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user.followers.remove(request.user)
    messages.warning(request, 'リムーブしました。')
    return safe_redirect(request, fallback='post:post_list')


@login_required
@require_POST
def follow_view(request, username):
    user = get_object_or_404(get_user_model(), username=username)
    user.followers.add(request.user)
    messages.success(request, 'フォローしました。')
    return safe_redirect(request, fallback='post:post_list')


@login_required
def edit_profile_icon(request):
    if request.method != 'POST':
        form = UploadProfileImgForm()
    else:
        form = UploadProfileImgForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            user.icon = form.cleaned_data['icon']
            user.save()
            messages.success(request, 'アイコンを変更しました。')
            return redirect('accounts:profile', user.username)
    return render(request, 'accounts/icon.html', {'form': form})


# ---------------------------------------------------------------------------
# ユーザー一覧（共通 Mixin でフォロー状態をコンテキストに注入）
# ---------------------------------------------------------------------------

class AccountListMixin(LoginRequiredMixin, ListView):
    """ユーザー一覧系ビューの共通基底クラス。"""
    template_name = 'accounts/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        return context


class AccountsListView(AccountListMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = 'ユーザー一覧'
        return context

    def get_queryset(self):
        qs = get_user_model().objects.all()
        q_word = self.request.GET.get('query')
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs


class FollowingListView(AccountListMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = f'@{self.kwargs.get("username", "")}さんのフォロー一覧'
        return context

    def get_queryset(self):
        target = get_object_or_404(get_user_model(), username=self.kwargs['username'])
        qs = target.following.all()
        q_word = self.request.GET.get('query')
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs


class FollowerListView(AccountListMixin):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = f'@{self.kwargs.get("username", "")}さんのフォロワー一覧'
        return context

    def get_queryset(self):
        target = get_object_or_404(get_user_model(), username=self.kwargs['username'])
        qs = target.followers.all()
        q_word = self.request.GET.get('query')
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs
