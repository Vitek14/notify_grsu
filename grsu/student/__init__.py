from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update

Base = declarative_base()

class Student(Base):
    """Класс студента определяет такие функции, как: auth(), get_user_info"""
    __tablename__ = "user_data"
    rowid = Column("rowid", Integer, primary_key=True, autoincrement=True)  # В SQLite3 по умолчанию есть первичный ключ, а именно rowid
    username = Column(String)
    password = Column(String)
    MDL_SSP_AuthToken = Column(String)
    MDL_SSP_SessID = Column(String)
    MOODLEID1_ = Column(String)
    MoodleSession = Column(String)
    tabnum = Column(String)
    lang = Column(String)
    group_0 = Column(Integer)
    group_1 = Column(Integer)
    group_2 = Column(Integer)
    group_3 = Column(Integer)
    group_4 = Column(Integer)
    group_5 = Column(Integer)
    tg_id = Column(Integer)

    from ._auth import auth, about
    from .data.select import get_login, get_groups, get_token, get_groups_all
    from ._parse_info import get_about, get_attestation

    def refresh_token(self, new_token: dict, tg_id: int) -> None:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        print("Обновление токена")
        with Session() as session:
            session.execute(update(Student).where(Student.tg_id == tg_id).values(new_token)) # type: ignore
            session.commit() 


    def check_if_exists(self, user_id: int) -> bool:
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
    

    def create_new_student(self, user_id: int, auth_info: dict, login: str, password: str) -> None:
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
