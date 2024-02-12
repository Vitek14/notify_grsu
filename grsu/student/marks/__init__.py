from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update

Base = declarative_base()

class Marks(Base):
    """Класс оценок студента"""
    __tablename__ = "grades"
    rowid = Column("rowid", Integer, primary_key=True, autoincrement=True)
    subject = Column(String)
    mark = Column(String)
    date = Column(String)
    user_id = Column(Integer)
    
    from ._marks import get_marks_from_site, get_courses_data, get_courses_names
    from ..data.select import get_marks
    from ..data.insert import insert_new_marks
    from ..data.delete import delete_marks
    