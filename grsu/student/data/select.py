from typing import Sequence
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)

# Объявляем объект сессии
Session = sessionmaker(engine)


# noinspection PyProtectedMember
class Mixin:
    """
    Представляет собой обёртку для основных классов Student и Marks
    """
    def get_login(self, tg_id: int) -> dict:
        """Получает данные о логине, пароле"""

        Student = self.__class__
        with Session() as session:
            result = session.execute(select(Student.username, Student.password)
                                     .where(Student.tg_id == tg_id)).first()._asdict()

        return result

    def get_token(self, tg_id: int) -> dict:
        """Получает данные о текущем сохранённом токене"""

        # Было бы неплохо поменять как-то
        Student = self.__class__
        with Session() as session:
            token_info = session.execute(select(Student.MDL_SSP_AuthToken, Student.MDL_SSP_SessID, Student.MOODLEID1_,
                                                Student.MoodleSession).where(Student.tg_id == tg_id)).first()._asdict()

        return token_info

    def get_groups(self, tg_id: int) -> dict:
        """
        Получает данные о группах студента.
        :param tg_id: ID пользователя в Telegram
        :return: Словарь со всеми группами студента в количестве 6 штук. Среди них может быть None,
        если у студента меньше 6 групп
        """

        # Получаем данные токена
        Student = self.__class__
        with Session() as session:
            groups_info = session.execute(select(Student.group_0, Student.group_1, Student.group_2,
                                                 Student.group_3, Student.group_4, Student.group_5)
                                          .where(Student.tg_id == tg_id)).first()._asdict()

        return groups_info

    def get_groups_all(self) -> Sequence:
        """
        :return: Возвращает группы всех студентов из базы данных.
        """
        Student = self.__class__
        with Session() as session:
            groups_info = session.execute(select(Student.group_0, Student.group_1, Student.group_2, Student.group_3,
                                                 Student.group_4, Student.group_5, Student.tg_id)).all()

        return groups_info

    def get_marks(self, user_id: int) -> Sequence:
        """
        :param user_id: ID пользователя в Telegram
        :return: Все оценки студента найденные в базе данных
        """

        Marks = self.__class__
        with Session() as session:
            marks = session.execute(select(Marks.subject, Marks.mark, Marks.date).where(Marks.user_id == user_id)).all()

        return marks
