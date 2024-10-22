from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from ..data.select import Mixin
from ._marks import MarksWebMixin
from ...student import Student
from aiohttp import ClientSession
from loguru import logger


Base = declarative_base()
student_cl = Student()


class Marks(Base, Mixin, MarksWebMixin):
    """
    Класс оценок студента
    """

    __tablename__ = "grades"
    rowid = Column("rowid", Integer, primary_key=True, autoincrement=True)
    subject = Column(String)
    mark = Column(String)
    date = Column(String)
    user_id = Column(Integer)
    
    from ._marks import get_marks_from_site, get_courses_data, get_courses_names
    # from ..data.select import get_marks
    from ..data.insert import insert_new_marks
    from ..data.delete import delete_marks

    # ЭКСПЕРИМЕНТАЛЬНО, работа продолжается
    async def notify_new_marks(self):
        async with ClientSession() as session:
            # Требуется получить данные для about и т.д...

            # Получение всех групп студента, а также td_id
            groups = self.get_groups_all()
            for student in groups:
                logger.warning("Может возникнуть ошибка в notify_new_marks: "
                               "tg_id не так определён")
                tg_id = student["tg_id"]
                token_info = self.get_token(tg_id)
                is_token_valid = student_cl.token_validity(token_info)
                if not is_token_valid:
                    login_info = student_cl.get_login(tg_id)
                    new_token = student_cl.auth(login_info["login"],login_info["password"])
                    student_cl.refresh_token(new_token, tg_id)
                    token_info = new_token

