from django.shortcuts import render, redirect

# Create your views here.

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from itertools import chain
from .models import Post


class PostListView(LoginRequiredMixin, ListView):
    template_name = 'post/post_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['User'] = self.request.user
        return context

    def get_queryset(self):
        user = self.request.user
        qs = Post.objects.filter(author__in=chain(
            user.following.all(), [user])).order_by('-created_at')
        return qs


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = "post/post_create.html"
    fields = ['content']
    success_url = reverse_lazy('post:post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)
