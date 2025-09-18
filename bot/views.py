from traceback import format_exc

from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from asgiref.sync import sync_to_async
from django.http import HttpRequest, JsonResponse
from django.conf import settings

from telebot.apihelper import ApiTelegramException
from telebot.types import Update, Message

from bot import bot, logger, RegisterStates

from .models import *
from .services.sending import *

@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    '''
        Установка вебхуков со стороны бота
    '''
    bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}", allowed_updates=['message', 'callback_query'])
    bot.send_message(settings.OWNER_ID, "webhook set")
    return JsonResponse({"message": "OK"}, status=200)


@csrf_exempt
@require_POST
@sync_to_async
def index(request: HttpRequest) -> JsonResponse:
    '''
        Установка вебхуков со стороны сайта
    '''
    if request.META.get("CONTENT_TYPE") != "application/json":
        return JsonResponse({"message": "Bad Request"}, status=403)

    json_string = request.body.decode("utf-8")
    update = Update.de_json(json_string)
    try:
        bot.process_new_updates([update])
    except ApiTelegramException as e:
        logger.error(f"Telegram exception. {e} {format_exc()}")
    except ConnectionError as e:
        logger.error(f"Connection error. {e} {format_exc()}")
    except Exception as e:
        bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)



@bot.message_handler(commands=['start'])
def message_start(message: Message):
    """
        Обработка команды старт для админа и обычного пользователя
    """
    if message.from_user.id == int(settings.OWNER_ID):
        if len(UserToSend.get_names()) > 0:
            text = 'Вот список зарегистрированных пользователей:'
            for user in UserToSend.get_names():
                text += f'\n<strong>{user}</strong>'
            text += '\n\nДля отправки сообщения всем пользователям отправьте команду \n<code>/send [Текст сообщения]</code>'
        else:
            text = 'Зарегистрированных пользователей нет. Добавьте их в админ-панели или попросите зарегистрироваться'
        
        bot.send_message(
            chat_id=message.chat.id,
            text=text,
            parse_mode='html'
        )
    
    else:
        if len(UserToSend.objects.filter(chat_id=message.chat.id)) == 0:
            bot.set_state(message.from_user.id, RegisterStates.fullname)
            bot.send_message(chat_id=message.chat.id, text='Отправьте ваше Ф.И.О. в формате: <code>Иванов Иван Иванович</code>', parse_mode='html')
        else:
            bot.send_message(chat_id=message.chat.id, text='Это тестовый бот для отправки сообщений', parse_mode='html')



@bot.message_handler(commands=['send'])
def message_send(message: Message):
    """
        Обработка отправки рассылки
    """
    if message.from_user.id == int(settings.OWNER_ID):
        text = message.text[5:]
        for user in UserToSend.objects.all():
            bot.send_message(chat_id=message.chat.id, text=sending(user=user, message_text=text, bot=bot), parse_mode='html')



@bot.message_handler()
def messages(message: Message):
    """
        Обработка регистрации пользователя
    """
    # Сохранение имени
    if bot.get_state(message.from_user.id) == RegisterStates.fullname.name:
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['fullname'] = message.text
    
        bot.set_state(message.from_user.id, RegisterStates.email)
        bot.send_message(
            chat_id=message.chat.id,
            text='Теперь отправьте Email в формате: <code>example@email.ru</code>',
            parse_mode='html'
            )
        
    # Проверка и сохранение Email
    elif bot.get_state(message.from_user.id) == RegisterStates.email.name:
        if message.text.count('@') == 1 and '.' in message.text:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                data['email'] = message.text
    
            bot.set_state(message.from_user.id, RegisterStates.phone)
            bot.send_message(
                chat_id=message.chat.id,
                text='Осталось отправить номер в формате: <code>+79999999999</code>',
                parse_mode='html'
                )
        
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text='Некорректный Email, отправьте в формате: <code>example@email.ru</code>',
                parse_mode='html'
                )
            
    # Проверка и сохранение номера
    elif bot.get_state(message.from_user.id) == RegisterStates.phone.name:
        if message.text.startswith('+') and 12 <= len(list(message.text)) <= 14:
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                print('OK')
                print(data)
                user = UserToSend(
                    fullname=data['fullname'],
                    chat_id=message.chat.id,
                    email=data['email'],
                    phone=message.text,
                )
                user.save()
            bot.delete_state(message.from_user.id, RegisterStates.phone)
            bot.send_message(
                chat_id=message.chat.id,
                text='Отлично, Вы успешно зарегистрированы!',
                parse_mode='html'
                )
        
        else:
            bot.send_message(
                chat_id=message.chat.id,
                text='Некорректный номер, отправьте в формате: <code>+79999999999</code>',
                parse_mode='html'
                )
        

        
 