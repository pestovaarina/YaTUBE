from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus

from ..models import Group, Post

User = get_user_model()


class PostURLSTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_url_exists_at_desired_location(self):
        """Страницы '/', '/group/test-slug/', '/profile/test-author/',
        '/posts/<post_id>/' доступны любому пользователю."""
        url_response = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/test-author/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for adress, response in url_response.items():
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.guest_client.get(adress).status_code, response
                )

    def test_url_exists_at_desired_location_authorized(self):
        """Страницы '/create/', '/posts/<post_id>/comment/'
        доступны авторизованному пользователю."""
        url_response = {
            '/create/': HTTPStatus.OK,
            f'/posts/{self.post.id}/comment/': HTTPStatus.OK,
        }
        for adress, response in url_response.items():
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.authorized_client.get(adress).status_code, response
                )

    def test_url_exists_at_desired_location_authorized(self):
        """Страница '/posts/<post_id>/edit' доступна автору поста."""
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_url_redirect_anonymous(self):
        """Страницы '/create/', '/posts/<post_id>/edit/',
        '/posts/<post_id>/comment/' перенаправляют
        анонимного пользователя на страницу '/login/'."""
        url_response = {
            '/create/',
            f'/posts/{self.post.id}/edit/',
            f'/posts/{self.post.id}/comment/',
        }
        for adress in url_response:
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress, follow=True)
                self.assertRedirects(response, '/auth/login/?next=' + adress)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/test-author/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.authorized_client.get(adress), template
                )
