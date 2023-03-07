from django.db import models

from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(
        verbose_name='Название группы',
        help_text='Введите название группы',
        max_length=200
    )
    slug = models.SlugField(
        verbose_name='URL страницы группы',
        unique=True
    )
    description = models.TextField(
        verbose_name='Описание группы',
        help_text='Введите описание группы'
    )

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст поста',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        on_delete=models.CASCADE,
        related_name='posts'
    )
    group = models.ForeignKey(
        Group,
        verbose_name='Группа',
        help_text='Группа, к которой будет относиться пост',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts'
    )
    image = models.ImageField(
        verbose_name='Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self) -> str:
        return self.text[:15]


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        verbose_name='Пост',
        related_name='comments',
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор комментария',
        related_name='comments',
        on_delete=models.CASCADE,
    )
    text = models.TextField(
        verbose_name='Текст комментария',
        help_text='Оставьте комментарий',
    )
    created = models.DateTimeField(
        verbose_name='Дата публикации',
        auto_now_add=True,
    )

    class Meta:
        ordering = ['-created', '-id']

    def __str__(self) -> str:
        return self.text[:15]


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        verbose_name='Подписчик',
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        verbose_name='Автор поста',
        on_delete=models.CASCADE,
        related_name='following'
    )
