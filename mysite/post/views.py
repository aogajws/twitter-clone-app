from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

from .models import Post, Like
from . import forms
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth import get_user_model

from itertools import chain


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'post/post_list.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['post_list'] = Post.objects.filter(author__in=chain(
            user.following.all(), [user])).order_by('-created_at')
        context['User'] = user
        context['description'] = 'タイムライン'
        liked_set = set()
        liked_count = [None] * len(context['post_list'])
        for i, post in enumerate(context['post_list']):
            if post.like_set.filter(user=user).exists():
                liked_set.add(post.pk)
            liked_count[i] = Like.objects.filter(post=post).count()
        context['liked_set'] = liked_set
        context['liked_count'] = liked_count
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
    like = Like.objects.filter(post=post, user=user)
    if like.exists():
        like.delete()
        messages.warning(request, 'いいねを取り消しました。')
    else:
        like.create(post=post, user=user)
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
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        liked_set = set()
        liked_count = [None] * len(context['post_list'])
        for i, post in enumerate(context['post_list']):
            if post.like_set.filter(user=context['User']).exists():
                liked_set.add(post.pk)
            liked_count[i] = Like.objects.filter(post=post).count()
        context['liked_set'] = liked_set
        context['liked_count'] = liked_count
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        qs = Post.objects.all().order_by('-created_at')
        if q_word:
            qs = qs.filter(content__contains=q_word)
        return qs


class PostStatus(DetailView):
    template_name = 'post/post_status.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        context['pk'] = self.kwargs.get('pk')
        post = get_object_or_404(Post, pk=context['pk'])
        parent = post.parent
        if parent:
            context['parent_post'] = parent
            context['parent_liked'] = parent.like_set.filter(
                user=context['User']).exists()
            context['parent_likes'] = Like.objects.filter(
                post=parent).count()
        else:
            context['parent_post'] = None
        context['post'] = post
        context['liked'] = post.like_set.filter(
            user=context['User']).exists()
        context['likes'] = Like.objects.filter(
            post=post).count()
        context['reply_list'] = Post.objects.filter(parent=post)
        reply_liked_set = set()
        reply_liked_count = [None] * len(context['reply_list'])
        for i, reply in enumerate(context['reply_list']):
            if reply.like_set.filter(user=context['User']).exists():
                reply_liked_set.add(reply.pk)
            reply_liked_count[i] = Like.objects.filter(post=reply).count()
        context['reply_liked_set'] = reply_liked_set
        context['reply_liked_count'] = reply_liked_count
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
    template_name = 'post/replies.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        liked_set = set()
        liked_count = [None] * len(context['post_list'])
        for i, post in enumerate(context['post_list']):
            if post.like_set.filter(user=context['User']).exists():
                liked_set.add(post.pk)
            liked_count[i] = Like.objects.filter(post=post).count()
        context['liked_set'] = liked_set
        context['liked_count'] = liked_count
        return context

    def get_queryset(self):
        qs = Post.objects.filter(
            Q(content__contains="@" + self.request.user.username + " ") |
            Q(content__contains="@" + self.request.user.username + "　") |
            Q(content__contains="@" + self.request.user.username + "\n") |
            Q(content__contains="@" + self.request.user.username + "\r") |
            Q(content__endswith="@" + self.request.user.username)
        ).order_by('-created_at')
        return qs


# class LikedAccountsListView(LoginRequiredMixin, ListView):
#     template_name = 'accounts/account_list.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['followings'] = self.request.user.following.all()
#         context['description'] = "いいねしたユーザー一覧"
#         return context

#     def get_queryset(self):
#         q_word = self.request.GET.get('query')
#         post = get_object_or_404(Post, pk=self.kwargs['pk'])
#         # liked_user = Like.objects.filter(post=post).values_list("user")
#         qs = get_user_model().like_set.filter(post=post)
#         if q_word:
#             qs = qs.filter(username__contains=q_word)
#         return qs
