from django.db import models


class UserToSend(models.Model):
    '''
        Модель пользователя для отправки сообщений    
    '''
    fullname = models.CharField(verbose_name='Ф.И.О. пользователя', max_length=128)
    chat_id = models.IntegerField(verbose_name='ID пользователя', null=True, blank=True)
    email = models.EmailField(verbose_name='Email пользователя', null=True, blank=True)
    phone = models.CharField(verbose_name='Телефон пользователя', max_length=15, null=True, blank=True)

    def __str__(self):
        return f'Пользователь {self.fullname}'
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def get_names():
        return UserToSend.objects.values_list('fullname', flat=True)
    
    def get_phones():
        return ";".join(UserToSend.objects.values_list('phone', flat=True))