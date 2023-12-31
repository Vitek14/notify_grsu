import grequests
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

# from main import attestation

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)

# Объявляем объект сессии
Session = sessionmaker(engine)

def get_login(self, tg_id: int) -> dict:
    """Получает данные о логине, пароле"""

    # Было бы неплохо поменять как-то
    Student = self.__class__
    with Session() as session:
        result = session.execute(select(Student.username, Student.password).where(Student.tg_id == tg_id)).first()._asdict() # type: ignore

    return result

def get_token(self, tg_id: int) -> dict:
    """Получает данные о текущем сохранённом токене"""

    # Было бы неплохо поменять как-то
    Student = self.__class__
    with Session() as session:
        token_info = session.execute(select(Student.MDL_SSP_AuthToken, Student.MDL_SSP_SessID, Student.MOODLEID1_, Student.MoodleSession).where(Student.tg_id == tg_id)).first()._asdict() # type: ignore

    return token_info

def get_groups(self, tg_id: int) -> dict:
    """Получает данные о группах студента"""

    # Получаем данные токена
    Student = self.__class__
    with Session() as session:
        groups_info = session.execute(select(Student.group_0, Student.group_1, Student.group_2, Student.group_3, Student.group_4, Student.group_5).where(Student.tg_id == tg_id)).first()._asdict() # type: ignore

    return groups_info
