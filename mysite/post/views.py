from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

from .models import Post
from . import forms
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.db.models import Q, Count, Case, When
from itertools import chain
from .models import Post
from . import forms


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'post/post_list.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        post_list = Post.objects.filter(author__in=chain(
            user.following.all(), [user])).prefetch_related('liked_users').order_by('-created_at').annotate(liked_count=Count("liked_users"))
        context['User'] = user
        context['description'] = 'タイムライン'
        liked = [None] * len(post_list)
        for i, post in enumerate(post_list):
            liked[i] = user in post.liked_users.all()
        context['zip'] = zip(post_list, liked)
        return context

    def get_queryset(self):
        user = self.request.user
        qs = Post.objects.filter(author__in=chain(
            user.following.all(), [user])).order_by('-created_at')
        return qs


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = forms.PostCreationForm
    template_name = "post/post_create.html"
    success_url = reverse_lazy("post:post_list")

    def form_valid(self, form):
        form.instance.author = self.request.user
        result = super().form_valid(form)
        messages.success(self.request, 'ツイートしました。')
        return result


def favorite_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    already_liked = user in post.liked_users.all()
    if already_liked:
        post.liked_users.remove(user)
        messages.warning(request, 'いいねを取り消しました。')
    else:
        post.liked_users.add(user)
        messages.success(request, 'いいねしました。')
    post.save()
    return redirect(request.META['HTTP_REFERER'])


def delete_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
        post.delete()
        messages.warning(request, 'ツイートを削除しました。')
    return redirect(request.META['HTTP_REFERER'])


class SearchPostListView(LoginRequiredMixin, ListView):
    template_name = 'post/search_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['User'] = user
        post_list = context['post_list']
        liked = [None] * len(post_list)
        for i, post in enumerate(post_list):
            liked_users = post.liked_users
            liked[i] = user in liked_users.all()
        context['zip'] = zip(post_list, liked)
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        qs = Post.objects.all().prefetch_related('liked_users').order_by(
            '-created_at').annotate(liked_count=Count("liked_users"))
        if q_word:
            qs = qs.filter(content__contains=q_word)
        return qs


class PostStatusView(DetailView):
    template_name = 'post/post_status.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['User'] = user
        context['pk'] = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=context['pk'])
        parent = post.parent
        if parent:
            context['parent_post'] = parent
            liked_users = parent.liked_users
            context['parent_liked'] = user in liked_users.all()
            context['parent_likes'] = liked_users.count()
        else:
            context['parent_post'] = None
        context['post'] = post
        liked_users = post.liked_users
        context['liked'] = user in liked_users.all()
        reply_list = Post.objects.filter(
            parent=post).prefetch_related('liked_users').annotate(liked_count=Count("liked_users"))
        reply_liked = [False] * len(reply_list)
        for i, reply in enumerate(reply_list):
            liked_users = reply.liked_users
            reply_liked[i] = user in liked_users.all()
        context['zip'] = zip(reply_list, reply_liked)
        return context


def reply_create_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = forms.PostCreationForm(request.POST or None)

    if request.method == 'POST':
        reply = form.save(commit=False)
        reply.author = request.user
        reply.parent = post
        reply.content = "@" + reply.parent.author.username + " " + reply.content
        reply.save()
        messages.success(request, '返信しました。')
        return redirect('post:post_list')

    context = {
        'form': form,
        'post': post
    }
    return render(request, 'post/post_create.html', context)


class ReplyPostListView(LoginRequiredMixin, ListView):
    template_name = 'post/reply_list.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['User'] = user
        post_list = context['post_list']
        liked = [False] * len(post_list)
        for i, post in enumerate(post_list):
            liked_users = post.liked_users
            liked[i] = user in liked_users.all()
        context['zip'] = zip(post_list, liked)
        return context

    def get_queryset(self):
        qs = Post.objects.filter(
            Q(content__contains="@" + self.request.user.username + " ") |
            Q(content__contains="@" + self.request.user.username + "　") |
            Q(content__contains="@" + self.request.user.username + "\n") |
            Q(content__contains="@" + self.request.user.username + "\r") |
            Q(content__endswith="@" + self.request.user.username)
        ).prefetch_related('liked_users').order_by('-created_at').annotate(liked_count=Count("liked_users"))
        return qs


class LikedAccountsListView(LoginRequiredMixin, ListView):
    template_name = 'accounts/account_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['followings'] = self.request.user.following.all()
        context['description'] = "いいねしたユーザー一覧"
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        qs = post.liked_users.all()
        if q_word:
            qs = qs.filter(username__contains=q_word)
        return qs
