import vk_api
from vk_api.longpoll import VkLongPoll
from config import group_token, sql_info
import sqlalchemy as sq
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, InvalidRequestError
from sqlalchemy import create_engine
from random import randrange

engine = create_engine(sql_info, client_encoding='utf8')
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()
connection = engine.connect()
vk = vk_api.VkApi(token=group_token)
longpoll = VkLongPoll(vk)


# БД пользователя ВК
class User(Base):
    __tablename__ = 'vk_user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)


# БД избранных анкет
class FavoritesUser(Base):
    __tablename__ = 'favorites_user'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True, nullable=False)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    id_user = sq.Column(sq.Integer,
                        sq.ForeignKey('vk_user.id', ondelete='CASCADE'))


# БД избранных фото
class FavoritPhotos(Base):
    __tablename__ = 'FavoritPhotos'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    link_photo = sq.Column(sq.String)
    count_likes = sq.Column(sq.Integer)
    id_favorites_user = sq.Column(sq.Integer,
                                  sq.ForeignKey('favorites_user.id',
                                                ondelete='CASCADE'))


# БД черного списка
class BlackList(Base):
    __tablename__ = 'black_list'
    id = sq.Column(sq.Integer, primary_key=True, autoincrement=True)
    vk_id = sq.Column(sq.Integer, unique=True)
    first_name = sq.Column(sq.String)
    second_name = sq.Column(sq.String)
    city = sq.Column(sq.String)
    link = sq.Column(sq.String)
    link_photo = sq.Column(sq.String)
    count_likes = sq.Column(sq.Integer)
    id_user = sq.Column(sq.Integer,
                        sq.ForeignKey('vk_user.id',
                                      ondelete='CASCADE'))


# Пишет сообщение пользователю
def write_msg(user_id, message, attachment=None):
    vk.method('messages.send', {'user_id': user_id,
                                'message': message,
                                'random_id': randrange(10 ** 7),
                                'attachment': attachment
                                })


# Регистрация пользователя в БД
def register_user(vk_id):
    try:
        new_user = User(
            vk_id=vk_id
        )
        session.add(new_user)
        session.commit()
        return True
    except (IntegrityError, InvalidRequestError):
        return False


# Проверка регистрации пользователя в БД
def check_db_master(ids):
    current_user_id = session.query(User).filter_by(vk_id=ids).first()
    return current_user_id


# Проверка людей в БД
def check_db_user(ids):
    favorits_user = session.query(FavoritesUser).filter_by(
        vk_id=ids).first()
    blocked_user = session.query(BlackList).filter_by(
        vk_id=ids).first()
    return favorits_user, blocked_user


# Добавляет человека в избранное
def add_user(event_id, vk_id, first_name, second_name, city, link, id_user):
    try:
        new_user = FavoritesUser(
            vk_id=vk_id,
            first_name=first_name,
            second_name=second_name,
            city=city,
            link=link,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Пользователь добавлен в избранное')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в избранном.')
        return False


# Добавляет фото избранного в БД
def add_user_photos(event_id, link_photo, count_likes, id_dating_user):
    try:
        new_user = FavoritPhotos(
            link_photo=link_photo,
            count_likes=count_likes,
            id_favorites_user=id_dating_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Фото пользователя сохранено в избранном')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Фото этого пользователя уже сохранено')
        return False


# Проверка есть ли человек в избранном
def check_db_favorites(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    alls_users = session.query(FavoritesUser).filter_by(id_user=current_users_id.id).all()
    return alls_users


# Удаляет человека из избранного
def delete_db_favorites(ids):
    current_user = session.query(FavoritesUser).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


# Добавление человека в черный список
def add_to_black_list(event_id, vk_id,
                      first_name, second_name,
                      city, link,
                      link_photo, count_likes, id_user):
    try:
        new_user = BlackList(
            vk_id=vk_id,
            first_name=first_name,
            second_name=second_name,
            city=city,
            link=link,
            link_photo=link_photo,
            count_likes=count_likes,
            id_user=id_user
        )
        session.add(new_user)
        session.commit()
        write_msg(event_id,
                  'Пользователь добавлен в черный список.')
        return True
    except (IntegrityError, InvalidRequestError):
        write_msg(event_id,
                  'Пользователь уже в черном списке.')
        return False


# Проверят есть ли человек в черном списке
def check_db_black(ids):
    current_users_id = session.query(User).filter_by(vk_id=ids).first()
    all_users = session.query(BlackList).filter_by(id_user=current_users_id.id).all()
    return all_users


# Удаляет человека из черного списка
def delete_db_blacklist(ids):
    current_user = session.query(BlackList).filter_by(vk_id=ids).first()
    session.delete(current_user)
    session.commit()


if __name__ == '__main__':
    Base.metadata.create_all(engine)
