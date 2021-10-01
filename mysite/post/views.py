from django.shortcuts import render, redirect

# Create your views here.

from .models import Post
from . import forms
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.contrib import messages

from itertools import chain


def post_list(request):
    if request.user.is_authenticated:
        user = request.user
        context = {
            'post_list': Post.objects.filter(author__in=chain(request.user.following.all(), [request.user])).order_by('-created_at'),
            'User': user,
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
    post.likes += 1
    post.save()
    messages.success(request, 'いいねしました。')
    return redirect(request.META['HTTP_REFERER'])


def delete(request, pk):
    post = Post.objects.get(pk=pk)
    if post.author == request.user:
        post.delete()
        messages.warning(request, 'ツイートを削除しました。')
    return redirect(request.META['HTTP_REFERER'])
