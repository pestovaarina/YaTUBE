from django.test import TestCase, Client
from http import HTTPStatus


class StaticPagesURLTests(TestCase):
    def setUp(self):
        # Создаем неавторизованый клиент
        self.guest_client = Client()

    def test_about_url(self):
        """Проверка доступности страниц."""
        url_response = [
            '/about/author/',
            '/about/tech/',
        ]
        for adress in url_response:
            with self.subTest(adress=adress):
                self.assertEqual(
                    self.guest_client.get(adress).status_code, HTTPStatus.OK
                )

    def test_about_url_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            'about/author.html': '/about/author/',
            'about/tech.html': '/about/tech/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                self.assertTemplateUsed(
                    self.guest_client.get(adress), template
                )
