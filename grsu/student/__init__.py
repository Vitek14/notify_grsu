from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy import update

Base = declarative_base()


class Student(Base):
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

    from ._auth import auth, about
    from .data.select import get_login, get_groups, get_token, get_groups_all
    from ._parse_info import get_about, get_attestation

    @staticmethod
    def refresh_token(new_token: dict, tg_id: int) -> None:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)

        # Объявляем объект сессии
        Session = sessionmaker(engine)
        print("Обновление токена")
        with Session() as session:
            session.execute(update(Student).where(Student.tg_id == tg_id).values(new_token))  # type: ignore
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

    @staticmethod  # Для более наглядного показа, что этот метод не зависит от класса по своей сути(экспериментально)
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
