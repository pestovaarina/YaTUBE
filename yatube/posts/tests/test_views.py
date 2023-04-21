import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django import forms

from ..models import Group, Post, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test-author')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.following_author = User.objects.create_user(
            username='following-author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Другое тестовое описание',
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post_image = uploaded
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый пост',
            image=cls.post_image,
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.author,
            post=cls.post,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username='NoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'),
            reverse(
                'posts:profile', kwargs={'username': self.user.username}): (
                'posts/profile.html'),
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}): (
                'posts/post_detail.html'),
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}): (
                'posts/create_post.html'),
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def post_check(self, post):
        """Функция проверки правильности содержимого поста."""
        post_text = post.text
        post_author = post.author
        post_group_slug = post.group
        post_image = post.image
        self.assertEqual(post_text, self.post.text)
        self.assertEqual(post_author, self.author)
        self.assertEqual(post_group_slug, self.post.group)
        self.assertEqual(post_image, f'posts/{self.post_image.name}')

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.post_check(first_object)

        page_title = response.context['title']
        self.assertEqual(page_title, 'Это главная страница проекта Yatube')

    def test_group_list_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.post_check(first_object)
        self.assertNotEqual(first_object.group.slug, self.another_group.slug)

        group_object = response.context['group']
        group_title = group_object.title
        group_desciption = group_object.description
        self.assertEqual(group_title, self.group.title)
        self.assertEqual(group_desciption, self.group.description)

        page_title = response.context['title']
        self.assertEqual(page_title, f'Записи сообщества {self.group.title}')

    def test_profile_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.author.username}))
        first_object = response.context['page_obj'][0]
        self.post_check(first_object)

        author_object = response.context['author']
        author_username = author_object.username
        self.assertEqual(author_username, self.author.username)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}))
        detailed_post = response.context['post']
        self.post_check(detailed_post)

        post_count_expected = response.context['post_count']
        post_number = Post.objects.filter(author=self.author).count()
        self.assertEqual(post_number, post_count_expected)

        first_comment = response.context['comments'][0]
        self.assertEqual(first_comment.text, self.comment.text)
        self.assertEqual(first_comment.author.username, self.author.username)
        self.assertEqual(first_comment.post.pk, self.post.pk)

    def form_fields_check(self, url):
        """Функция проверки типов полей формы."""
        response = self.author_client.get(url)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        self.form_fields_check(reverse('posts:post_create'))

    def test_edit_page_show_correct_context(self):
        """Шаблон post_create на странице редактирования записи
        сформирован с правильным контекстом."""
        self.form_fields_check(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        response = self.author_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk})
        )
        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_post_with_group_show_on_correct_pages(self):
        """Новый пост с группой отображается на правильных страницах."""
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertIn(self.post, response.context['page_obj'])

        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.author.username}))
        self.assertIn(self.post, response.context['page_obj'])

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        self.assertIn(self.post, response.context['page_obj'])

        response = self.authorized_client.get(
            reverse('posts:group_list',
                    kwargs={'slug': self.another_group.slug}))
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_post_detail_shows_new_comment(self):
        """Шаблон post_detail отображает новый комментарий."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        self.assertIn(self.comment, response.context['comments'])

    def test_index_cache(self):
        """Шаблон страницы index хранит записи в кеше"""
        post_cache = Post.objects.create(
            author=self.user,
            text='Тестовый пост для проверки кеша',
        )
        response = self.authorized_client.get(
            reverse('posts:index')
        )
        post_cache.delete()
        new_response = self.authorized_client.get(
            reverse('posts:index')
        )
        self.assertEqual(response.content, new_response.content)

    def test_authorized_user_follow_author(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following_author.username}))
        self.assertTrue(Follow.objects.filter(
            user=self.user, author=self.following_author
        ).exists())

    def test_authorized_user_follow_author(self):
        """Авторизованный пользователь может отписываться
        от других пользователей."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following_author.username}))
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.following_author.username}))
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=self.following_author
        ).exists())

    def test_follower_see_new_post(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.following_author.username}))
        new_post = Post.objects.create(
            author=self.following_author,
            text='Тестовый пост',
        )
        response = self.authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertIn(new_post, response.context['page_obj'])

    def test_not_follower_dont_see_new_post(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        new_post = Post.objects.create(
            author=self.following_author,
            text='Тестовый пост',
        )
        other_user = User.objects.create_user(username='other_user')
        other_authorized_client = Client()
        other_authorized_client.force_login(other_user)
        response = other_authorized_client.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(new_post, response.context['page_obj'])


class PaginatorViewsTest(TestCase):
    NUM_OF_POSTS = 13
    NUM_OF_POSTS_ON_PAGES = [10, 3]

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
        for i in range(cls.NUM_OF_POSTS):
            cls.post = Post.objects.create(
                author=cls.author,
                group=cls.group,
                text='Тестовый пост',
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка работы пагинатора:
        верное количество постов на страницах
        и содержимое постов."""
        pages_urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.author})
        ]
        for page in range(len(self.NUM_OF_POSTS_ON_PAGES)):
            for url in pages_urls:
                with self.subTest(url=url):
                    response = self.client.get(url + f'?page={page+1}')
                    self.assertEqual(len(response.context['page_obj']),
                                     self.NUM_OF_POSTS_ON_PAGES[page])
                    post_list = response.context.get('page_obj').object_list
                    first_post = post_list[0]
                    post_text = first_post.text
                    post_author = first_post.author
                    post_group_slug = first_post.group
                    self.assertEqual(post_text, self.post.text)
                    self.assertEqual(post_author, self.author)
                    self.assertEqual(post_group_slug, self.post.group)
