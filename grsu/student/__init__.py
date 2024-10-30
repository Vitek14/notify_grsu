from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column, Session
from sqlalchemy import create_engine, select
from sqlalchemy import update
from .data.select import Mixin
from .data.student_info.select import SelectInfoMixin
from ._parse_info import ParseMixin
from ._auth import AboutMixin
from loguru import logger
from settings import base_engine  # TODO: МОЖЕТ БЫТЬ ОШИБКА

logger.warning("Внимание, используется экспериментальный импорт из настроек (base_engine)")
from aiohttp import ClientSession

Base = declarative_base()
engine = create_engine(base_engine)
Base.metadata.create_all(engine)


class Student(Base, Mixin, ParseMixin, AboutMixin):
    """Класс студента определяет такие функции, как: auth(), get_user_info"""
    __tablename__ = "user_data"

    rowid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str]
    password: Mapped[str]
    MDL_SSP_AuthToken: Mapped[str]
    MDL_SSP_SessID: Mapped[str]
    MOODLEID1_: Mapped[str]
    MoodleSession: Mapped[str]
    tabnum: Mapped[str]
    lang: Mapped[str]
    group_0: Mapped[int]
    group_1: Mapped[int]
    group_2: Mapped[int]
    group_3: Mapped[int]
    group_4: Mapped[int]
    group_5: Mapped[int]
    tg_id: Mapped[int]

    def __encrypt_data(self, data: dict, password: str) -> None:
        """
        Зашифрует данные для последующего внесения в базу данных.
        :param password: Пароль шифрования.
        :param data: Словарь для шифрования
        """
        pass

    def token_validity(self, token_info: dict) -> bool:
        """
        Проверит токен на 'валидность'.
        :param token_info: Информация о токене пользователя.
        :return: True или False в зависимости от верности токена.
        """

        about_info = self.about(token_info)
        # СЛЕДУЮЩИЙ КОД ВЗЯТ ИЗ main.py(А точнее функции /info)
        try:
            # Проверяем что в about_info существует полезная информация, иначе токен устарел
            about_info["userInfo"]
        except KeyError:
            return False
        return True

    @staticmethod
    def refresh_token(new_token: dict, tg_id: int) -> None:

        # Объявляем объект сессии
        print("Обновление токена")
        with Session(engine) as session:
            session.execute(update(Student).where(Student.tg_id == tg_id).values(new_token))
            session.commit()

    @staticmethod
    def check_if_exists(user_id: int) -> bool:
        with Session(engine) as session:
            student_exist = session.query(Student).filter_by(tg_id=user_id).first()
            if student_exist:
                return True
            else:
                return False

    # @staticmethod
    def check_groups_info(self, user_id: int) -> bool:
        """
        Проверит правильные ли данные групп студента.
        :param user_id: ID Telegram пользователя для проверки.
        :return: True или False в зависимости от верности данных групп(и лабораторных в т.ч)
        """
        # self.get_token()
        pass

    @staticmethod
    def refresh_groups_info(user_id: int) -> None:
        """
        Обновит данные групп студента
        :param user_id: ID Telegram пользователя для обновления.
        """
        pass

    @staticmethod
    def create_new_student(user_id: int, auth_info: dict, login: str, password: str) -> None:
        about_info = Student().about(auth_info)
        about_info["tg_id"] = user_id
        about_info["username"] = login
        about_info["password"] = password
        with Session() as session:
            new_student = Student(**about_info)
            session.add(new_student)
            session.commit()


class StudentInfo(Base, SelectInfoMixin):
    """Класс базовой информации о студенте, например ФИО, Факультет, Специальность и т.д"""
    __tablename__ = "user_info"

    rowid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    surname: Mapped[str]
    name: Mapped[str]
    patronymic: Mapped[str]
    faculty: Mapped[str]
    specialization: Mapped[str]
    internal_email: Mapped[str]
    group_text: Mapped[str]
    course_text: Mapped[str]
    language_code: Mapped[int]
    main_group: Mapped[int]
    subgroup_1: Mapped[int]
    subgroup_2: Mapped[int]
    subgroup_3: Mapped[int]
    subgroup_4: Mapped[int]
    subgroup_5: Mapped[int]
    subgroup_6: Mapped[int]
    tg_id: Mapped[int]

    @staticmethod
    def create_info(info: [dict[str, str | int]]) -> None:
        with Session() as session:
            info = Student(**info)
            session.add(info)
            session.commit()

    @staticmethod
    def basic_info_exists(tg_id: int) -> bool:
        """
        Вернёт информацию о том, существует ли базовая информация в базе данных.
        :param tg_id: Telegram ID пользователя.
        :return: True или False в зависимости от наличия информации в базе данных
        """
        with Session() as session:
            info_exist = session.query(StudentInfo).filter_by(tg_id=tg_id).first()
            if info_exist:
                return True
            else:
                return False
