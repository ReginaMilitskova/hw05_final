from django.test import TestCase

from ..models import Group, Post, User


class PostModelTest(TestCase):
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
            author=cls.user,
            text='Привет, мир!',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        object_title = {
            self.post.text[:15]: self.post,
            self.group.title: self.group
        }
        for expected_object_name, obj_model in object_title.items():
            with self.subTest(object=obj_model):
                self.assertEqual(expected_object_name, str(obj_model))

    def test_correct_object_verbose_name(self):
        """Проверяем, что verbose_name в полях совпадает с ожидаемым."""
        post_field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор поста',
            'group': 'Группа',
        }
        group_field_verboses = {
            'title': 'Название группы',
            'slug': 'URL страницы группы',
            'description': 'Описание группы',
        }
        verboses_fields = {
            self.post: post_field_verboses,
            self.group: group_field_verboses,
        }

        for obj_model, verboses_field in verboses_fields.items():
            for field, expected_value in verboses_field.items():
                with self.subTest(object=obj_model, field=field):
                    self.assertEqual(
                        obj_model._meta.get_field(field).verbose_name,
                        expected_value
                    )

    def test_correct_object_help_text(self):
        """help_text в полях совпадает с ожидаемым"""
        post_field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }
        group_field_help_texts = {
            'title': 'Введите название группы',
            'description': 'Введите описание группы',
        }
        field_help_texts = {
            self.post: post_field_help_texts,
            self.group: group_field_help_texts,
        }

        for obj_model, fields_help in field_help_texts.items():
            for field, expected_value in fields_help.items():
                with self.subTest(object=obj_model, field=field):
                    self.assertEqual(
                        obj_model._meta.get_field(field).help_text,
                        expected_value
                    )
