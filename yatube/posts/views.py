from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .models import Group, Post, Follow, Comment, User
from .forms import PostForm, CommentForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

from yatube.settings import POSTS_PER_PAGE, CACHE_TIME


def pagination(request, posts):
    paginator = Paginator(posts, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj

@cache_page(CACHE_TIME, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = pagination(request, posts)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_list(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = pagination(request, posts)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    page_obj = pagination(request, posts)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user__exact=request.user, author__exact=author
        ).exists()
        if request.user != author.username:
            non_author = True
        else:
            non_author = False
    else:
        following = False
        non_author = False
    context = {
        'author': author,
        'page_obj': page_obj,
        'following': following,
        'non_author': non_author,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    comments = Comment.objects.filter(post_id__exact=post.pk)
#    comments = post.comments.all()
    comment_form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'is_author': post.author == request.user,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/post_create.html'
    form = PostForm(request.POST or None)
    if form.is_valid():
        create_post = form.save(commit=False)
        create_post.author = request.user
        create_post.save()
        return redirect('posts:profile', create_post.author)

    context = {'form': form,}
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    template = 'posts/post_create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('post:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, context)

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    follow_posts = Post.objects.filter(
        author__following__user=request.user
    )
    page_obj = pagination(request, follow_posts)
    context = {
        'page_obj': page_obj
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author.username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', author.username)
