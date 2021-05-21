import vk_api

from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard
import pymorphy2
from data import db_session
from data.__all_models import *
import random
import string
from datetime import datetime
from copy import deepcopy
from constants import *


def text_to_seconds(text):
    try:
        date, time = text.split()
        d, m, y = map(int, date.split('.'))
        h, mt = map(int, time.split(':'))
        try:
            dt = datetime(year=y, month=m, day=d, hour=h, minute=mt)
            seconds = dt.timestamp()
            return seconds
        except Exception as ex:
            return 'Некорректная дата или время'
    except Exception as ex:
        return 'Некорректный формат даты или времени'


def main():
    morph = pymorphy2.MorphAnalyzer()
    db_session.global_init('school_db')
    db_sess = db_session.create_session()

    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, -VK_ID)

    keyboard = VkKeyboard()
    keyboard.add_button('Мероприятия', color='primary')
    user_keyboard = keyboard.get_keyboard()

    admin_keyboard = deepcopy(keyboard)
    admin_keyboard.add_line()
    admin_keyboard.add_button('Добавить', color='positive')
    admin_keyboard.add_button('Удалить', color='negative')
    admin_keyboard = admin_keyboard.get_keyboard()

    cancel_keyboard = VkKeyboard()
    cancel_keyboard.add_button('Отмена', color='negative')
    cancel_keyboard = cancel_keyboard.get_keyboard()

    for event in longpoll.listen():
        if event.type == VkBotEventType.MESSAGE_NEW:
            vk_id = event.obj.message['from_id']
            admin = db_sess.query(Admin).filter(Admin.vk_id == vk_id).first()
            text = event.obj.message['text']

            params = {'user_id': vk_id,
                      'random_id': random.randint(0, 2 ** 64),
                      'message': ''}
            attachments = []
            if admin:
                admin_event = db_sess.query(Event). \
                    filter(Event.owner == vk_id, Event.is_added.is_(False)).first()
                if admin.status == 0:
                    if text == 'Добавить':
                        admin.status = 1
                        if not admin_event:
                            params['message'] = 'Для добавления мероприятия ' \
                                                'перешлите запись из данного сообщества ' \
                                                'о мероприятии в переписку'
                            new_event = Event(owner=vk_id,
                                              is_added=False)
                            db_sess.add(new_event)
                        else:
                            params['message'] = 'Нельзя добавлять два мероприятия одновременно'
                    elif text == 'Удалить':
                        admin.status = 2
                        params['message'] = 'Для удаления мероприятия из списка' \
                                            ' перешлите запись о мероприятии в переписку'
                elif admin.status == 1:
                    if text == 'Отмена':
                        params['message'] = 'Вы больше не добавляете мероприятие'
                        admin.status = 0
                        db_sess.query(Event).filter(Event.id == admin_event.id).delete()
                    else:
                        if not admin_event.post_id:
                            is_added = False
                            response_attachments = event.obj.message['attachments']
                            ts = datetime.now().timestamp()
                            current_events = db_sess.query(Event).filter(Event.is_added.is_(True),
                                                                         Event.time_to > ts)
                            for a in response_attachments:
                                if a['type'] == 'wall':
                                    wall = a['wall']
                                    if wall['to_id'] == VK_ID:
                                        wall_id = wall['id']
                                        in_list = False
                                        for ce in current_events:
                                            if ce.post_id == wall_id:
                                                in_list = True
                                                break
                                        if not in_list:
                                            admin_event.post_id = wall_id
                                            is_added = True
                                            break
                            if is_added:
                                params['message'] = 'Отлично. ' \
                                                    'Теперь отправьте дату начала мероприятия ' \
                                                    'в формате |ДД.ММ.ГГГГ ЧЧ:ММ|'
                            else:
                                params['message'] = 'Вы не отправили корректную ' \
                                                    'запись из данного сообщества'
                        elif not admin_event.time_from:
                            r = text_to_seconds(text)
                            if isinstance(r, str):
                                params['message'] = f'{r}. Попробуйте ещё раз. ' \
                                                    f'Формат |ДД.ММ.ГГГГ ЧЧ:ММ|'
                            else:
                                admin_event.time_from = r
                                params['message'] = 'Отлично. ' \
                                                    'Теперь отправьте дату конца мероприятия ' \
                                                    'в формате |ДД.ММ.ГГГГ ЧЧ:ММ|'

                        elif not admin_event.time_to:
                            r = text_to_seconds(text)
                            if isinstance(r, str):
                                params['message'] = f"{r}. Попробуйте ещё раз"
                            else:
                                admin_event.time_to = r
                                params['message'] = 'Запись добавлена в мероприятия'
                                admin_event.is_added = True
                                admin.status = 0
                elif admin.status == 2:
                    if text == 'Отмена':
                        params['message'] = 'Вы больше не удаляете мероприятие'
                        admin.status = 0
                    else:
                        is_deleted = False
                        response_attachments = event.obj.message['attachments']
                        for a in response_attachments:
                            if a['type'] == 'wall':
                                wall = a['wall']
                                if wall['to_id'] == VK_ID:
                                    wall_id = wall['id']
                                    db_sess.query(Event).filter(Event.post_id == wall_id).delete()
                                    is_deleted = True
                                    break
                        if is_deleted:
                            params['message'] = 'Мероприятие удалено'
                            admin.status = 0
                        else:
                            params['message'] = 'Вы не отправили запись из списка мероприятий'
            if not params['message']:
                if text == 'Начать':
                    params['message'] = 'Привет! Нажми кнопку \"Мероприятия\", чтоб узнать' \
                                        ' о событиях, которые скоро пройдут в школе'
                elif text == 'Мероприятия':
                    timestamp = datetime.now().timestamp()
                    attachments = db_sess.query(Event).filter(Event.is_added.is_(True),
                                                              Event.time_to > timestamp).all()
                    if not attachments:
                        params['message'] = 'Нет доступных мероприятий'
                elif text.startswith(PREFIX):
                    line = text.lstrip(PREFIX)
                    c, *c_params = line.split()
                    if c == 'get_admin':
                        if len(c_params) != 1:
                            params['message'] = 'Неверные параметры'
                        else:
                            key = c_params[0]
                            free_key = db_sess.query(Key).filter(Key.key == key).first()
                            if free_key:
                                if admin:
                                    params['message'] = 'Вы уже администратор'
                                else:
                                    user = Admin(vk_id=vk_id, status=0)
                                    db_sess.add(user)
                                    db_sess.delete(free_key)
                                    params['message'] = 'Вы стали администратором'
                            else:
                                params['message'] = 'Неверный ключ'
                    elif c == 'create_key':
                        if admin:
                            new_key = ''.join(random.choice(string.ascii_letters) for _ in range(10))
                            key = Key(key=new_key)
                            db_sess.add(key)
                            params['message'] = f'Новый ключ - {new_key}'
                        else:
                            params['message'] = 'У вас нет доступа к этой команде'
                    else:
                        params['message'] = 'Такой команды нет'
                else:
                    params['message'] = 'Некорректный ввод'
            if admin:
                if admin.status in [1, 2]:
                    params['keyboard'] = cancel_keyboard
                else:
                    params['keyboard'] = admin_keyboard
            else:
                params['keyboard'] = user_keyboard
            if attachments:
                attachments.sort(key=lambda at: at.time_to)
                for a in attachments:
                    ts = datetime.now().timestamp()
                    message = ''
                    if a.time_from <= ts <= a.time_to:
                        message = 'Уже идет! 🔥'
                    elif ts < a.time_from:
                        days = (a.time_from - ts) // (60 * 60 * 24) + 1
                        w = morph.parse('день')[0]
                        message = f'Начнется через {int(days)} ' \
                                  f'{w.make_agree_with_number(days).word} ' \
                                  f'{random.choice("😀😄😋🤯🤪🥳😸✌✌️")}'

                    vk.messages.send(user_id=params['user_id'],
                                     random_id=params['random_id'],
                                     attachment=f'wall-{-VK_ID}_{a.post_id}',
                                     message=message)
                    params['random_id'] = random.randint(0, 2 ** 64)
            else:
                vk.messages.send(**params)
            db_sess.commit()


if __name__ == "__main__":
    main()
