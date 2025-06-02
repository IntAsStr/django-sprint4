from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

from django.urls import reverse_lazy, reverse
from django.core.paginator import Paginator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.auth import get_user_model

from .models import Category, Post, Comments
from .forms import EditProfileForm, PostCreateForm, CommentsForm

User = get_user_model()


class MainPage(ListView):
    model = Post
    template_name = 'blog/index.html'
    queryset = Post.objects.select_related('author')
    ordering = 'id'
    paginate_by = 10


def post_detail(request, id):
    template = 'blog/detail.html'

    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        id=id,
        
        is_published=True,
        category__is_published=True
    )

    comments = post.comments.select_related('author')

    context = {
        'post': post,
        'form': CommentsForm(),
        'comments': comments
        }
    return render(request, template, context)


class CategoryPost(ListView):
    template_name = 'blog/category.html'
    ordering = 'id'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True
        )
        return Post.objects.filter(
            category=self.category,
            is_published=True,
            pub_date__lt=timezone.now()
        ).select_related('author', 'category',)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = 10
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        username = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        # Получаем посты пользователя
        posts_list = user.posts.select_related('category').filter(
            is_published=True,
        ).order_by('-pub_date')

        # Пагинация
        paginator = Paginator(posts_list, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': page_obj.has_other_pages(),
        })
        return context


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user


class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
        )

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class EditProfile(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = User
    form_class = EditProfileForm
    template_name = 'blog/user.html'
    success_url = reverse_lazy('blog:profile')

    def get_success_url(self):
        # Перенаправляем на профиль текущего пользователя
        return reverse(
            'blog:profile', kwargs={'username': self.request.user.username}
            )

    def test_func(self):
        return self.request.user == self.get_object()

    def get_object(self, queryset=None):
        return self.request.user


class PostEdit(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Post
    form_class = PostCreateForm


class DeletePost(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:profile')


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentsForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.add_comment = post
        comment.save()
    return redirect('blog:post_detail', id=pk)


class EditCommentView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Comments
    form_class = CommentsForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return super().get_queryset().filter(
            author=self.request.user,
            add_comment_id=self.kwargs['post_id'],
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class DeleteCommentView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Comments
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail', kwargs={'id': self.object.add_comment.id}
        )
