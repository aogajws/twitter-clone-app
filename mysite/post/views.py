from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

from .models import Post, Like
from . import forms
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView
from django.contrib import messages

from itertools import chain


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'post/post_list.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        likedlist = []
        for post in context['post_list']:
            if post.like_set.filter(user=self.request.user).exists():
                likedlist.append(post.pk)
        context['liked_list'] = likedlist
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


def favorite(request, pk):
    post = Post.objects.get(pk=pk)
    user = request.user
    like = Like.objects.filter(post=post, user=user)
    if like.exists():
        like.delete()
        post.likes -= 1
        messages.warning(request, 'いいねを取り消しました。')
    else:
        like.create(post=post, user=user)
        post.likes += 1
        messages.success(request, 'いいねしました。')
    post.save()
    return redirect(request.META['HTTP_REFERER'])


def delete(request, pk):
    post = Post.objects.get(pk=pk)
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
        likedlist = []
        for post in context['post_list']:
            if post.like_set.filter(user=self.request.user).exists():
                likedlist.append(post.pk)
        context['liked_list'] = likedlist
        return context

    def get_queryset(self):
        q_word = self.request.GET.get('query')
        qs = Post.objects.all().order_by('-created_at')
        if q_word:
            qs = qs.filter(content__contains=q_word)
        return qs


class PostStatus(DetailView):
    """ツイート詳細"""
    template_name = 'post/post_status.html'
    model = Post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        context['pk'] = self.kwargs.get('pk')
        likedlist = []
        if post.like_set.filter(user=self.request.user).exists():
            likedlist.append(post.pk)
        context['liked_list'] = likedlist
        # どのコメントにも紐づかないコメント=記事自体へのコメント を取得する
        context['reply_list'] = self.object.reply_set.filter(
            parent__isnull=True)
        return context


def reply_create(request, post_pk):
    """記事へのコメント作成"""
    post = get_object_or_404(Post, pk=post_pk)
    form = forms.ReplyForm(request.POST or None)

    if request.method == 'POST':
        reply = form.save(commit=False)
        reply.post = post
        reply.save()
        return redirect('post:post_detail', pk=post.pk)

    context = {
        'form': form,
        'post': post
    }
    return render(request, 'post/post_status.html', context)
