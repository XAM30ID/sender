import requests
import os
from dotenv import load_dotenv

from django.conf import settings
from django.core.mail import send_mail
from telebot import TeleBot

from ..models import UserToSend

load_dotenv()


def sending(user: UserToSend, message_text: str, bot: TeleBot):
    '''
        Функция для отправки сообщений пользователю во всех вариантах (Email, SMS, Telegram)
        И формирование отчётного сообщения
    '''
    text = f'Отправка рассылки пользователю: {user.fullname}'

    # Email
    try:
        send_mail(
            'Тест',
            message_text,
            settings.EMAIL_HOST_USER,
            [user.email],
            fail_silently=False,
        )
        text += f'\n✅ Успешная отправка на Email: {user.email}'
    except Exception as e:
        text += f'\n❌ Не удалось отправить на Email: {user.email}'
        print('Ошибка при отправке Email: ', e)

    # Telegram
    try:
        bot.send_message(text=message_text, chat_id=user.chat_id)
        text += f'\n✅ Успешная отправка в телеграм: {user.fullname}'
    except Exception as e:
        text += f'\n❌ Не удалось отправить в телеграм: {user.fullname}'
        print('Ошибка при отправке Telegram: ', e)

    # SMS
    try:
        login = os.getenv('SMSC_LOGIN')
        password = os.getenv('SMSC_PASSWORD')
        phones = user.phone
        message = message_text
        
        url = f"https://smsc.ru/sys/send.php?login={login}&psw={password}&phones={phones}&mes={message}"
        response = requests.get(url)

        text += f'\n✅ Успешная отправка sms: {user.phone}'
    except Exception as e:
        text += f'\n❌ Не удалось отправить sms: {user.phone}'
        print('Ошибка при отправке SMS: ', e)

    return text
