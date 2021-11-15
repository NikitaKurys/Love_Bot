import vk_api
import datetime
from vk_api.longpoll import VkLongPoll
import json
from sql import engine, Session
from config import group_token, my_token

vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)
session = Session()
connection = engine.connect()


def search_users(sex, age_from, age_to, city):
    users_info = []
    vk1 = vk_api.VkApi(token=my_token)
    link_profile = 'https://vk.com/id'
    search = vk1.method('users.search', {'sort': 1,
                                         'sex': sex,
                                         'v': '5.131',
                                         'age_from': age_from,
                                         'age_to': age_to,
                                         'has_photo': 1,
                                         'count': 20,
                                         'status': 1,
                                         'hometown': city,
                                         })
    for elements in search['items']:
        if elements['is_closed'] is False:
            user = [
                elements['first_name'],
                elements['last_name'],
                link_profile + str(elements['id']),
                elements['id']
            ]
            users_info.append(user)
        else:
            continue
    return users_info


def search_photo(owner_id):
    vk1 = vk_api.VkApi(token=my_token)
    try:
        search = vk1.method('photos.get', {'access_token': my_token,
                                           'v': '5.131',
                                           'owner_id': owner_id,
                                           'album_id': 'profile',
                                           'count': 10,
                                           'extended': 1,
                                           'photo_sizes': 0
                                           })
    except vk_api.exceptions.ApiError:
        return 'Нет доступа к фото'
    users_photos = []
    for i in range(10):
        try:
            users_photos.append(
                [search['items'][i]['likes']['count'],
                 'photo' + str(search['items'][i]['owner_id'])
                 + '_' + str(search['items'][i]['id'])])
        except IndexError:
            users_photos.append(['нет фото.'])
    return users_photos


def sort_photos(photos):
    result = []
    for element in photos:
        if element != ['нет фото.'] and photos != 'нет доступа к фото':
            result.append(element)
    return sorted(result)


def json_create(list):
    today = datetime.date.today()
    today_str = f'{today.day}.{today.month}.{today.year}'
    res_dict = {}
    res_list = []
    for num, info in enumerate(list):
        res_dict['data'] = today_str
        res_dict['first_name'] = info[0]
        res_dict['second_name'] = info[1]
        res_dict['link'] = info[2]
        res_dict['id'] = info[3]
        res_list.append(res_dict.copy())

    with open("info.json", "a", encoding='UTF-8') as file:
        json.dump(res_list, file, ensure_ascii=False)

    print('Информация успешно записана в json файл.')
