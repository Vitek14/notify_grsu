from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy import update
from .data.select import Mixin
from ._parse_info import ParseMixin
from ._auth import AboutMixin

Base = declarative_base()


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

    def check_token(self, user_id: int) -> bool:
        """
        Проверит токен на 'валидность'.
        :param user_id: ID Telegram пользователя.
        :return: True или False в зависимости от верности токена.
        """
        pass

    @staticmethod
    def refresh_token(new_token: dict, tg_id: int) -> None:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)

        # Объявляем объект сессии
        Session = sessionmaker(engine)
        print("Обновление токена")
        with Session() as session:
            session.execute(update(Student).where(Student.tg_id == tg_id).values(new_token))
            session.commit() 

    @staticmethod
    def check_if_exists(user_id: int) -> bool:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
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
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        about_info = Student().about(auth_info)
        about_info["tg_id"] = user_id
        about_info["username"] = login
        about_info["password"] = password
        with Session() as session:
            new_student = Student(**about_info)
            session.add(new_student)
            session.commit()
