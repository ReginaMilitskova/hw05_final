from django.forms import ModelForm

from .models import Post, Comment
from django.utils.translation import gettext_lazy as _


class PostForm(ModelForm):
    class Meta():
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': _('Текст поста'),
            'group': _('Группа'),
            'image': _('Картинка'),
        }
        help_texts = {
            'text': _('Введите текст'),
            'group': _('Выберите группу'),
            'image': _('Добавьте картинку'),
        }


class CommentForm(ModelForm):
    class Meta():
        model = Comment
        fields = (
            'text',
        )
        labels = {
            'text': _('Текст комментария'),
        }
        help_texts = {
            'text': _('Добавьте комментарий'),
        }
