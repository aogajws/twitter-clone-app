from django.shortcuts import render, redirect

# Create your views here.

from .models import Post, Like
from . import forms
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib import messages

from itertools import chain


def post_list(request):
    if request.user.is_authenticated:
        user = request.user
        postlist = Post.objects.filter(author__in=chain(
            request.user.following.all(), [request.user])).order_by('-created_at')
        likedlist = []
        for post in postlist:
            if post.like_set.filter(user=request.user).exists():
                likedlist.append(post.pk)
        context = {
            'post_list': postlist,
            'liked_list': likedlist,
            'User': user,
            'description': 'タイムライン'
        }
    else:
        context = {}
    return render(request, 'post/post_list.html', context)


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
