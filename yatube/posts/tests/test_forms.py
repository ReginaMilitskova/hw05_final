import tempfile
import shutil

from posts.models import Post, Group, Comment, User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from yatube.settings import BASE_DIR
from django.core.files.uploadedfile import SimpleUploadedFile
from posts.forms import CommentForm
from django.core.cache import cache

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
#        cls.user_two = User.objects.create_user(username='Other')

        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test_slug',
            description='Тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Привет, мир!',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
#        self.other_user = Client()
#        self.other_user.force_login(self.user_two)
        cache.clear()

    def test_post_create(self):
        """Валидная форма создает запись в Post
        авторизованным пользователем."""
        post_count = Post.objects.count()

        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.id,
            'image': self.uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response,
                             reverse('posts:profile',
                                     args=(self.user.username)))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group,
                image='posts/small.gif'
            ).exists()
        )
        print(self.post.image)

    def test_post_edit(self):
        """Валидная форма сохраняет отредактированный автором пост."""
        post = Post.objects.create(
            text='Привет, мир!',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Привет, мир! Как дела?',
            'group': post.group.id,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
            is_edit=True,
        )
        redirect = reverse(
            'posts:post_detail',
            kwargs={'post_id': post.id})
        self.assertRedirects(response, redirect)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=post.group.id,
                author=self.user
            ).exists()
        )

    def test_anon_user_cant_post_create(self):
        """Анонимный пользователь не может создать пост."""
        form_data = {
            'text': 'Этот пост не должен быть создан',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        expected_url = (reverse('users:login') + '?next='
                        + reverse('posts:post_create'))
        self.assertRedirects(response, expected_url)

    def test_anon_user_cant_post_edit(self):
        """Анонимный пользователь
        не может редактировать пост."""
        post = Post.objects.create(
            text='Редактирование поста',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Измененный пост',
            'group': self.group.id
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=self.group.id,
            ).exists()
        )
        expected_url = (reverse('users:login') + '?next='
                        + reverse('posts:post_edit',
                                  kwargs={'post_id': post.id}))
        self.assertRedirects(response, expected_url)

    def test_autorized_not_allowed_edit_form(self):
        """Авторизованный пользователь
        не может редактировать чужой пост."""
        post = Post.objects.create(
            text='Редактирование чужого поста',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'Отредактированный чужой пост',
            'group': self.group.id
        }
        response = self.other_user.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
            is_edit=True,
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
            ).exists()
        )
        expected_url = (
            reverse('posts:post_detail', kwargs={'post_id': post.id})
        )
        self.assertRedirects(response, expected_url)


class CommentFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = CommentForm
        cls.user = User.objects.create_user(username='Name')

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
        )
    
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
    
    def test_anon_user_cant_comments(self):
        """Анонимный пользователь не может оставлять комментарии"""
        guest_client = Client()
        text = 'Этот комментарий не должен быть создан'

        response = guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data={'text': text},
            follow=True,
        )
        expected_url = (
            reverse('users:login')
            + '?next='
            + reverse('posts:add_comment', kwargs={'post_id': self.post.id})
        )

        self.assertRedirects(response, expected_url)
        self.assertEqual(Comment.objects.count(), 0)

    def test_create_comment_auth(self):
        """Проверка создания комментария авторизованным пользователем."""
        post_new = Post.objects.create(
            author=self.user,
            text='Текст',
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_new.pk}),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_new.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        last_comment = Comment.objects.order_by('-pk')[0]
        self.assertEqual(last_comment.text, form_data['text'])
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post_new.pk}),
        )
        self.assertEqual(response.context['comments'][0].text, form_data['text'])
