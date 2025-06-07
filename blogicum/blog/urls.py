from django.urls import path

from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.MainPage.as_view(), name='index'),
    path('posts/<int:post_id>/', views.post_detail, name='post_detail'),
    path(
        'category/<slug:category_slug>/',
        views.CategoryPost.as_view(),
        name='category_posts'),
    path(
        'profile/<slug:username>/',
        views.UserProfileView.as_view(),
        name='profile'),
    path('posts/create/', views.PostCreateView.as_view(), name='create_post'),
    path('edit-profile/', views.EditProfile.as_view(), name='edit_profile'),
    path(
        'posts/<int:post_id>/edit/',
        views.PostEdit.as_view(),
        name='edit_post'),
    path(
        'posts/<int:id>/delete/',
        views.DeletePost.as_view(),
        name='delete_post'),
    path('posts/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path(
        'posts/<int:post_id>/comments/<int:pk>/edit_comment/',
        views.EditCommentView.as_view(),
        name='edit_comment'),
    path(
        'posts/<int:post_id>/delete_comment/<int:pk>/',
        views.DeleteCommentView.as_view(),
        name='delete_comment'
    )
]
