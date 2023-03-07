from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, User


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

        self.clients = {
            'guest_client': self.guest_client,
            'authorized_client': self.authorized_client,
        }

    def test_urls_available_to_any_client(self):
        """Страницы, доступные любому пользователю."""
        urls = [
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.pk}/',
        ]

        for client in self.clients:
            for url in urls:
                with self.subTest(client=client, url=url):
                    response = self.clients[client].get(url)
                    self.assertEqual(response.status_code, 200)

    def test_urls_available_to_auth_client(self):
        """Страницы, доступные только авторизованному пользователю."""
        following = User.objects.create_user(username='another_user')
        urls = [
            '/create/',
            f'/posts/{self.post.id}/edit/',
            '/follow/',
            f'/profile/{following.username}/follow/',
            f'/profile/{following.username}/unfollow/',
        ]
        clients = [
            'guest_client',
            'authorized_client',
        ]

        for url in urls:
            for client in clients:
                with self.subTest(client=client, url=url):
                    response = self.clients[client].get(url, follow=True)
                    if client == 'guest_client':
                        expected_url = reverse('users:login') + f'?next={url}'
                        self.assertRedirects(response, expected_url)
                    else:
                        self.assertEqual(response.status_code, 200)

    def test_guest_urls_uses_correct_template(self):
        """URL-адреса для гостя используют соответствующий шаблон."""
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', args=(
                    self.group.slug,)): 'posts/group_list.html',
            reverse(
                'posts:profile', args=(
                    self.user.username,)): 'posts/profile.html',
            reverse(
                'posts:post_detail', args=(
                    self.post.id,)): 'posts/post_detail.html'
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_auth_urls_uses_correct_template(self):
        """URL-адреса для авторизованного пользователя
        используют соответствующий шаблон."""
        templates_url_names = {
            reverse(
                'posts:post_edit', args=(
                    self.post.id,)): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
            reverse('posts:follow_index'): 'posts/follow.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_non_exist_url(self):
        """Проверка запроса к несуществующей странице"""
        non_exist_url = '/non_exist_url/'
        with self.subTest(non_exist_url=non_exist_url):
            response = self.authorized_client.get(non_exist_url)
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, 'core/404.html')
