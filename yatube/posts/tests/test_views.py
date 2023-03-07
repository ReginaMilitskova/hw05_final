import random
import shutil
import tempfile

from django import forms
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from yatube.settings import POSTS_PER_PAGE, BASE_DIR
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
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
            group=cls.group,
            text='Привет, мир!',
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
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': PostsPagesTests.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': PostsPagesTests.user.username}):
            'posts/profile.html',
            reverse('post:post_detail',
                    kwargs={'post_id': PostsPagesTests.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostsPagesTests.post.id}):
            'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        test_objects = {
            response.context['page_obj'][0]: PostsPagesTests.post,
            response.context['page_obj'][0].image: PostsPagesTests.post.image
        }
        for test_object, send_object in test_objects.items():
            with self.subTest(test_object=test_object):
                self.assertEqual(test_object, send_object)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group_list', args=(
                PostsPagesTests.group.slug,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)
        test_objects = {
            response.context['page_obj'][0]: PostsPagesTests.post,
            response.context['group']: PostsPagesTests.group,
            response.context['page_obj'][0].image: PostsPagesTests.post.image
        }
        for test_object, send_object in test_objects.items():
            with self.subTest(test_object=test_object):
                self.assertEqual(test_object, send_object)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', args=(
                PostsPagesTests.user.username,)))
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        test_objects = {
            response.context['page_obj'][0]: PostsPagesTests.post,
            response.context['author']: PostsPagesTests.user,
            response.context['page_obj'][0].image: PostsPagesTests.post.image
        }
        for test_object, send_object in test_objects.items():
            with self.subTest(test_object=test_object):
                self.assertEqual(test_object, send_object)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.guest_client.get(
            reverse('posts:post_detail', args=(
                PostsPagesTests.post.id,)))
        self.assertIn('post', response.context)
        post_detail_object = response.context['post']
        test_objects = {
            post_detail_object: PostsPagesTests.post,
            post_detail_object.group: PostsPagesTests.group,
            post_detail_object.image: PostsPagesTests.post.image
        }
        for test_object, send_object in test_objects.items():
            with self.subTest(test_object=test_object):
                self.assertEqual(test_object, send_object)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_index_page_cache(self):
        """Тест работы кэша"""
        post = Post.objects.create(
            author=PostsPagesTests.user,
            text='Тест кэша',
            group=PostsPagesTests.group
        )

        url = reverse('posts:index')
        response = self.guest_client.get(url)
        post.delete()
        response_2 = self.guest_client.get(url)
        self.assertEqual(response.content, response_2.content)

        cache.clear()
        response_3 = self.guest_client.get(url)
        self.assertNotEqual(response_2.content, response_3.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='following')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_follow(self):
        """Авторизованный пользователь может подписаться
        на других пользователей."""
        author_user = User.objects.create_user(username='author_user')
        test_count_1 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.authorized_client.get(
            reverse(
                'posts:profile_follow', args=(
                    author_user.username,)))
        test_count_2 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.assertEqual(test_count_1 + 1, test_count_2)

    def test_unfollow(self):
        """Авторизованный пользователь может отписаться
        от других пользователей."""
        author_user = User.objects.create_user(username='author_user')
        Follow.objects.create(user=FollowTests.user, author=author_user)
        test_count_1 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow', args=(
                    author_user.username,)))
        test_count_2 = Follow.objects.filter(
            user=FollowTests.user, author=author_user).count()
        self.assertEqual(test_count_1 - 1, test_count_2)

    def test_follower_view(self):
        """Новая запись пользователя появляется
        в ленте тех, кто на него подписан."""
        author_user = User.objects.create_user(username='author_user')
        test_post = Post.objects.create(
            author=author_user,
            text='Тестовый текст'
        )
        Follow.objects.create(user=FollowTests.user, author=author_user)
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertIn(test_post, response.context['page_obj'])

    def test_not_follower_view(self):
        """Новая запись пользователя не появляется
        в ленте тех, кто на него не подписан."""
        author_user = User.objects.create_user(username='author_user')
        test_post = Post.objects.create(
            author=author_user,
            text='Тестовый пост'
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index'))
        self.assertNotIn(test_post, response.context['page_obj'])


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        test_post_number = random.randint(
            POSTS_PER_PAGE + 2, POSTS_PER_PAGE * 2)

        cls.user = User.objects.create_user(username='post_author')
        cls.group = Group.objects.create(
            title='Тестовый текст',
            slug='Slug-test',
            description='Описание тестовое',
        )
        for i in range(test_post_number):
            Post.objects.bulk_create(
                [Post(
                    text='Текст',
                    author=cls.user,
                    group=cls.group
                )]
            )

    def setUp(self):
        cache.clear()

    def test_pagination(self):
        """Тестирование Пагинатора."""
        first_page_posts = POSTS_PER_PAGE
        total_posts = Post.objects.count()
        second_page_posts = total_posts - first_page_posts
        test_addresses = [
            reverse('posts:index'),
            reverse(
                'posts:group_list', args=(
                    PaginatorTest.group.slug,)),
            reverse(
                'posts:profile', args=(
                    PaginatorTest.user.username,))
        ]
        page_numbers = {
            1: first_page_posts,
            2: second_page_posts
        }
        for address in test_addresses:
            with self.subTest(address=address):
                for page_number, page in page_numbers.items():
                    response = self.client.get(
                        address, {'page': page_number}
                    )
                    self.assertEqual(len(
                        response.context['page_obj']), page
                    )
