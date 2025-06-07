from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.generic import (
    CreateView, DeleteView, DetailView, ListView, UpdateView
)

# Локальные импорты
from .forms import CommentsForm, EditProfileForm, PostCreateForm
from .models import Category, Comment, Post

User = get_user_model()


def permission_denied_view(request, exception=None):
    return HttpResponseForbidden("Доступ запрещён")


class MainPage(ListView):
    model = Post
    template_name = 'blog/index.html'
    ordering = '-pub_date'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.select_related('author', 'category').filter(
            Q(is_published=True) | Q(author=self.request.user)
            if self.request.user.is_authenticated else Q(is_published=True)
        ).filter(
            category__is_published=True,
            pub_date__lt=timezone.now(),
            is_published=True
        ).annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')
        return queryset


def post_detail(request, post_id):
    try:
        post = get_object_or_404(
            Post.objects.select_related('author', 'category', 'location'),
            id=post_id
        )

        if not post.is_published and post.author != request.user:
            raise Http404("Пост не найден или снят с публикации")

    except Post.DoesNotExist:
        raise Http404("Пост не найден")

    comments = post.comments.select_related('author').order_by('created_at')

    context = {
        'post': post,
        'form': CommentsForm(),
        'comments': comments
    }
    return render(request, 'blog/detail.html', context)


class CategoryPost(ListView):
    template_name = 'blog/category.html'
    ordering = 'id'
    paginate_by = 10

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['category_slug'],
            is_published=True,
        )

        # Базовый запрос
        queryset = Post.objects.filter(
            category=self.category,
            pub_date__lt=timezone.now(),
            is_published=True,
        ).select_related('author', 'category').annotate(
            comment_count=Count('comments')
        )

        # Условия видимости
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(is_published=True) | Q(author=self.request.user)
            )
        else:
            queryset = queryset.filter(is_published=True)

        return queryset.order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


class UserProfileView(DetailView):
    model = User
    template_name = 'blog/profile.html'
    context_object_name = 'profile'
    paginate_by = 10
    slug_field = 'username/'
    slug_url_kwarg = 'username'

    def get_object(self, queryset=None):
        username = self.kwargs.get(self.slug_url_kwarg)
        return get_object_or_404(User, username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object

        posts_list = user.posts.select_related('category').annotate(
            comment_count=Count('comments')
        ).order_by('-pub_date')

        paginator = Paginator(posts_list, self.paginate_by)
        page_number = self.request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        context.update({
            'page_obj': page_obj,
            'paginator': paginator,
            'is_paginated': page_obj.has_other_pages(),
        })
        return context


class OnlyAuthorMixin(UserPassesTestMixin):

    def test_func(self):
        objective = self.get_object()
        return objective.author == self.request.user


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
        form.instance.pub_date = timezone.now()
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


class PostEdit(UpdateView):
    model = Post
    form_class = PostCreateForm
    template_name = 'blog/create.html'
    pk_url_kwarg = 'post_id'

    def dispatch(self, request, *args, **kwargs):
        # Перенаправляем неавторизованных пользователей
        if not request.user.is_authenticated:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])

        # Проверяем, что автор поста - текущий пользователь
        post = self.get_object()
        if post.author != request.user:
            return redirect('blog:post_detail', post_id=kwargs['post_id'])

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('blog:post_detail', kwargs={'post_id': self.object.id})

    def form_valid(self, form):
        if not form.instance.pub_date:
            form.instance.pub_date = timezone.now()
        return super().form_valid(form)


class DeletePost(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Post
    success_url = reverse_lazy('blog:profile')
    pk_url_kwarg = 'id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    form = CommentsForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('blog:post_detail', post_id=pk)


class EditCommentView(LoginRequiredMixin, OnlyAuthorMixin, UpdateView):
    model = Comment
    form_class = CommentsForm
    template_name = 'blog/comment.html'
    pk_url_kwarg = 'pk'

    def get_queryset(self):
        return super().get_queryset().filter(
            author=self.request.user,
            post_id=self.kwargs['post_id'],
        )

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment'] = self.object
        return context


class DeleteCommentView(LoginRequiredMixin, OnlyAuthorMixin, DeleteView):
    model = Comment
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse_lazy(
            'blog:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


def logout_user(request):
    logout(request)
    return redirect(reverse('blog:index'))
