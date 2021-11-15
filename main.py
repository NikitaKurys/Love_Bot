import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_func import search_users, search_photo, sort_photos, json_create
from sql import engine, Session, write_msg, register_user, \
    add_user, add_user_photos, add_to_black_list, \
    check_db_user, check_db_black, check_db_favorites, \
    check_db_master, delete_db_blacklist, delete_db_favorites
from config import group_token

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
session = Session()
connection = engine.connect()


def work_bot():
    for this_event in longpoll.listen():
        if this_event.type == VkEventType.MESSAGE_NEW and this_event.to_me:
            message_text = this_event.text.title()
            return message_text, this_event.user_id


def menu_bot(id_num):
    write_msg(id_num,
              "Привет, это Love_Bot\n"
              "\nБот ищет людей для знакомства\n"
              "Для регистрации введите - 'Регистрация'.\n"
              "\n 2) Если вы уже зарегистрированы - начинайте поиск.\n"
              "Для поиска введите: пол мин.возраст-макс.возраст город\n"
              "например: девушка 18-25 москва\n"
              "\n 3) Перейти в избранное нажмите - 2\n"
              "\n 4) Перейти в черный список - 0\n")


def reg_new_user(id_num):
    write_msg(id_num, 'Вы прошли регистрацию.')
    write_msg(id_num, "Love_Bot - для активации бота\n")
    register_user(id_num)


def show_info():
    write_msg(user_id, 'Это была последняя анкета.'
                       '\nПерейти в избранное - 2'
                       '\nПерейти в черный список - 0'
                       '\nПоиск: пол мин.возраст-макс.возраст город'
                       '\nнапример: девушка 18-25 москва'
                       '\nМеню бота - Love_Bot')


def go_to_favorites(ids):
    alls_users = check_db_favorites(ids)
    write_msg(ids, 'Избранные анкеты:')
    for nums, users in enumerate(alls_users):
        write_msg(ids, f'{users.first_name}, '
                       f'{users.second_name}, '
                       f'{users.link}')
        write_msg(ids, '1 - Удалить из избранного, '
                       '0 - Далее '
                       '\n5 - Выход')
        msg_texts, user_ids = work_bot()
        if msg_texts == '0':
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, 'Это была последняя анкета.\n'
                                    'Love_bot - вернуться в меню\n')
            # Удаляем анкету из избранного
        elif msg_texts == '1':
            delete_db_favorites(users.vk_id)
            write_msg(user_ids, 'Анкета успешно удалена.')
            if nums >= len(alls_users) - 1:
                write_msg(user_ids, 'Это была последняя анкета.\n'
                                    'Love_Bot - вернуться в меню\n')
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'Love_Bot - для активации бота.')
            break


def go_to_blacklist(ids):
    all_users = check_db_black(ids)
    write_msg(ids, 'Анкеты в черном списке:')
    for num, user in enumerate(all_users):
        write_msg(ids, f'{user.first_name}, {user.second_name}, {user.link}')
        write_msg(ids, '1 - Удалить из черного списка, 0 - Далее \n5- Выход')
        msg_texts, user_ids = work_bot()
        if msg_texts == '0':
            if num >= len(all_users) - 1:
                write_msg(user_ids, 'Это была последняя анкета.\n'
                                    'Love_Bot - вернуться в меню\n')
            # Удалить анкету с ЧС
        elif msg_texts == '1':
            print(user.id)
            delete_db_blacklist(user.vk_id)
            write_msg(user_ids, 'Анкета успешно удалена')
            if num >= len(all_users) - 1:
                write_msg(user_ids, 'Это была последняя анкета.\n'
                                    'Love_Bot - вернуться в меню\n')
        elif msg_texts.lower() == 'q':
            write_msg(ids, 'Love_Bot - для активации бота.')
            break


if __name__ == '__main__':
    while True:
        msg_text, user_id = work_bot()
        if msg_text == "Love_Bot":
            menu_bot(user_id)
            msg_text, user_id = work_bot()
            # Регистрация пользователя в БД
            if msg_text.lower() == 'Регистрация':
                reg_new_user(user_id)
            elif len(msg_text) > 1:
                sex = 0
                if msg_text[0:7].lower() == 'девушка':
                    sex = 1
                elif msg_text[0:7].lower() == 'мужчина':
                    sex = 2
                age_at = msg_text[8:10]
                if int(age_at) < 16:
                    write_msg(user_id,
                              'Рановато Вам пользоваться данным ботом:) '
                              'минимальный возраст будет выставлен 16')
                    age_at = 16
                age_to = msg_text[11:14]
                if int(age_to) >= 90:
                    write_msg(user_id,
                              'Поздновато Вам пользоваться данным ботом:) '
                              'максимальный возраст будет выставлен 89')
                    age_to = 89
                city = msg_text[14:len(msg_text)].lower()
                # Поиск анкет по критериям
                result = search_users(sex, int(age_at), int(age_to), city)
                json_create(result)
                current_user_id = check_db_master(user_id)
                for i in range(len(result)):
                    dating_user, blocked_user = check_db_user(result[i][3])
                    # Сортировка фото по лайкам
                    user_photo = search_photo(result[i][3])
                    if user_photo == 'нет доступа к фото' or \
                            dating_user is not None or \
                            blocked_user is not None:
                        continue
                    sorted_user_photo = sort_photos(user_photo)
                    write_msg(user_id, f'\n{result[i][0]}  '
                                       f'{result[i][1]}  '
                                       f'{result[i][2]}', )
                    try:
                        write_msg(user_id, 'фото:',
                                  attachment=','.join
                                  ([sorted_user_photo[-1][1],
                                    sorted_user_photo[-2][1],
                                    sorted_user_photo[-3][1]]))
                    except IndexError:
                        for photo in range(len(sorted_user_photo)):
                            write_msg(user_id, 'фото:',
                                      attachment=sorted_user_photo[photo][1])
                    write_msg(user_id, '1 - Добавить,'
                                       '\n2 - Заблокировать,'
                                       '\n0 - Далее, '
                                       '\n5 - выход из поиска')
                    msg_text, user_id = work_bot()
                    if msg_text == '0':
                        if i >= len(result) - 1:
                            show_info()
                    # Добавить человека в избранное
                    elif msg_text == '1':
                        if i >= len(result) - 1:
                            show_info()
                            break
                        try:
                            add_user(user_id, result[i][3], result[i][1],
                                     result[i][0], city, result[i][2],
                                     current_user_id.id)
                            add_user_photos(user_id, sorted_user_photo[0][1],
                                            sorted_user_photo[0][0],
                                            current_user_id.id)
                        except AttributeError:
                            write_msg(user_id, 'Вы не зарегистрировались!'
                                               '\nВведите Love_Bot')
                            break
                    # Добавить человека в чс
                    elif msg_text == '2':
                        if i >= len(result) - 1:
                            show_info()
                        add_to_black_list(user_id, result[i][3], result[i][1],
                                          result[i][0], city, result[i][2],
                                          sorted_user_photo[0][1],
                                          sorted_user_photo[0][0],
                                          current_user_id.id)
                    elif msg_text.lower() == '5':
                        write_msg(user_id, 'Введите Love_Bot ')
                        break
        # Избранное
        elif msg_text == '2':
            go_to_favorites(user_id)
        # Черный список
        elif msg_text == '0':
            go_to_blacklist(user_id)
