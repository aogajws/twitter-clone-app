from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.db.models import Q, Count
from itertools import chain

from .models import Post
from . import forms
from common.utils import safe_redirect, LikedPostMixin


# ---------------------------------------------------------------------------
# タイムライン
# ---------------------------------------------------------------------------

class PostListView(LoginRequiredMixin, LikedPostMixin, ListView):
    template_name = 'post/post_list.html'
    model = Post

    def get_queryset(self):
        user = self.request.user
        return (
            Post.objects
            .filter(author__in=chain(user.following.all(), [user]))
            .select_related('author', 'repost_parent__author')
            .prefetch_related('liked_users', 'replies', 'reposted')
            .annotate(
                liked_count=Count('liked_users'),
                reply_count=Count('replies'),
                repost_count=Count('reposted'),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)  # LikedPostMixin が zip をセット
        context['User'] = self.request.user
        context['description'] = 'タイムライン'
        return context


# ---------------------------------------------------------------------------
# 投稿作成
# ---------------------------------------------------------------------------

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = forms.PostCreationForm
    template_name = 'post/post_create.html'
    success_url = reverse_lazy('post:post_list')
    description = 'ツイートの作成'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['description'] = self.description
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        result = super().form_valid(form)
        messages.success(self.request, 'ツイートしました。')
        return result


# ---------------------------------------------------------------------------
# いいね・削除
# ---------------------------------------------------------------------------

@login_required
@require_POST
def favorite_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    if user in post.liked_users.all():
        post.liked_users.remove(user)
        messages.warning(request, 'いいねを取り消しました。')
    else:
        post.liked_users.add(user)
        messages.success(request, 'いいねしました。')
    return safe_redirect(request)


@login_required
@require_POST
def delete_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
        messages.warning(request, 'ツイートを削除しました。')
    return safe_redirect(request)


# ---------------------------------------------------------------------------
# 検索
# ---------------------------------------------------------------------------

class SearchPostListView(LoginRequiredMixin, LikedPostMixin, ListView):
    template_name = 'post/search_list.html'

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        qs = (
            Post.objects.all()
            .select_related('author', 'repost_parent__author')
            .prefetch_related('liked_users', 'replies', 'reposted')
            .annotate(
                liked_count=Count('liked_users'),
                reply_count=Count('replies'),
                repost_count=Count('reposted'),
            )
        )
        if q_word:
            qs = qs.filter(content__contains=q_word)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        return context


# ---------------------------------------------------------------------------
# 投稿詳細（ステータス）
# ---------------------------------------------------------------------------

class PostStatusView(DetailView):
    template_name = 'post/post_status.html'
    model = Post

    def get_queryset(self):
        # parent と repost_parent を JOIN で取得してクエリを削減
        return (
            Post.objects
            .select_related(
                'author',
                'parent__author',
                'repost_parent__author',
            )
            .prefetch_related('liked_users', 'replies', 'reposted')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # self.object は DetailView が既にセット済み（二重クエリ不要）
        post = self.object
        context['User'] = user
        context['post'] = post

        # いいね関連（annotate で取得できないカウントは直接引く）
        liked_post_ids = (
            set(user.favorite_posts.values_list('pk', flat=True))
            if user.is_authenticated else set()
        )
        context['liked'] = post.pk in liked_post_ids
        context['likes'] = post.liked_users.count()
        context['reply_count'] = post.replies.count()
        context['repost_count'] = post.reposted.count()

        # 返信元投稿
        parent = post.parent
        if parent:
            context['parent_post'] = parent
            context['parent_liked'] = parent.pk in liked_post_ids
            context['parent_likes'] = parent.liked_users.count()
            context['parent_reply_count'] = parent.replies.count()
            context['parent_repost_count'] = parent.reposted.count()
        else:
            context['parent_post'] = None

        # 返信・リツイート一覧（N+1 を一括取得で解消）
        reply_list = (
            (post.replies.all() | post.reposted.all())
            .select_related('author', 'repost_parent__author')
            .prefetch_related('liked_users', 'replies', 'reposted')
            .annotate(
                liked_count=Count('liked_users'),
                reply_count=Count('replies'),
                repost_count=Count('reposted'),
            )
        )
        context['zip'] = zip(
            reply_list,
            [reply.pk in liked_post_ids for reply in reply_list],
        )
        return context


# ---------------------------------------------------------------------------
# 返信作成
# ---------------------------------------------------------------------------

@login_required
def reply_create_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = forms.PostCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        reply = form.save(commit=False)
        reply.author = request.user
        reply.parent = post
        reply.content = f'@{post.author.username} {reply.content}'
        reply.save()
        messages.success(request, '返信しました。')
        return redirect('post:post_list')

    context = {
        'form': form,
        'post': post,
        'description': '返信の作成',
    }
    return render(request, 'post/post_create.html', context)


# ---------------------------------------------------------------------------
# 返信一覧（自分へのメンション）
# ---------------------------------------------------------------------------

class ReplyPostListView(LoginRequiredMixin, LikedPostMixin, ListView):
    template_name = 'post/reply_list.html'
    model = Post

    def get_queryset(self):
        username = self.request.user.username
        return (
            Post.objects
            .filter(
                Q(content__contains=f'@{username} ') |
                Q(content__contains=f'@{username}\u3000') |  # 全角スペース
                Q(content__contains=f'@{username}\n') |
                Q(content__contains=f'@{username}\r') |
                Q(content__endswith=f'@{username}')
            )
            .select_related('author', 'repost_parent__author')
            .prefetch_related('liked_users', 'replies', 'reposted')
            .annotate(
                liked_count=Count('liked_users'),
                reply_count=Count('replies'),
                repost_count=Count('reposted'),
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        return context


# ---------------------------------------------------------------------------
# いいねしたユーザー一覧
# ---------------------------------------------------------------------------

class LikedAccountsListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        context['description'] = 'いいねしたユーザー一覧'
        return context

    def get_queryset(self):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        qs = post.liked_users.all().prefetch_related('following')
        q_word = self.request.GET.get('query')
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs


# ---------------------------------------------------------------------------
# リツイート作成
# ---------------------------------------------------------------------------

@login_required
def repost_create_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = forms.PostCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        repost = form.save(commit=False)
        repost.author = request.user
        repost.repost_parent = post
        repost.save()
        messages.success(request, 'リツイートしました。')
        return redirect('post:post_list')

    context = {
        'form': form,
        'post': post,
        'description': 'リツイートの作成',
    }
    return render(request, 'post/post_create.html', context)
