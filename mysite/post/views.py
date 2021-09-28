from django.shortcuts import render, redirect

# Create your views here.

from .models import Post
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import CreateView
from django.contrib.auth import get_user_model

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
    template_name = "post/post_create.html"
    fields = ['content']
    success_url = reverse_lazy('post:post_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


def favorite(request, pk):
    post = Post.objects.get(pk=pk)
    post.likes += 1
    post.save()
    return redirect(request.META['HTTP_REFERER'])
