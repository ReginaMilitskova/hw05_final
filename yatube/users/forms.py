from django.contrib.auth.forms import UserCreationForm
from posts.models import User

from django.utils.translation import gettext_lazy as _


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
        labels = {
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'username': _('Логин'),
            'email': _('Email'),
        }
        help_texts = {
            'first_name': _('Имя'),
            'last_name': _('Фамилия'),
            'username': _('Логин'),
            'email': _('Электронная почта'),
        }
