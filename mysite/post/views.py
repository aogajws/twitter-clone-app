from django.shortcuts import get_object_or_404, render, redirect

# Create your views here.

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib import messages
from django.contrib.auth import get_user_model
from itertools import chain
from .models import Post, Like
from . import forms


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'post/post_list.html'

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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        liked_set = []
        liked_count = [None] * len(context['post_list'])
        for i, post in enumerate(context['post_list']):
            if post.like_set.filter(user=self.request.user).exists():
                liked_set.append(post.pk)
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
