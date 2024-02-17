from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update, insert, select

from grsu.student import Student

Base = declarative_base()

class Schedule(Base):
    """Класс расписания определяет общее расписание студентов, а также их домашние задания"""
    __tablename__ = "schedule"
    rowid = Column("rowid", Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    lesson_type = Column(String)
    place = Column(String)
    room = Column(String)
    teacher = Column(String)
    date = Column(String)
    day = Column(Integer)
    start_time = Column(String)
    end_time = Column(String)
    group_id = Column(Integer)
    subgroup_id = Column(Integer)
    homework = Column(String)
    homework_added_by_id = Column(Integer)

    def if_exists(self, group_id: int) -> bool:
        """
        Функция проверит существует ли расписание для группы
        :group_id: Id группы
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
            schedule_exist = session.query(Schedule).filter_by(group_id=group_id).first()
            if schedule_exist:
                return True
            else:
                return False

    from ._web import get_raw_schedule, process_schedule

    def get_schedule_from_db(self) -> list:
        """
        Функция выдаёт всё расписание по группе
        :group_id: ID группы, для которого искать расписание
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
            # schedule = session.query(Schedule).filter_by(Schedule.group_id=group_id).all()
            schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
            Schedule.place, Schedule.room, Schedule.teacher, Schedule.date, Schedule.day, Schedule.start_time  ,
            Schedule.end_time, Schedule.group_id, Schedule.subgroup_id)).all()
        return schedule

    def create_schedule(self, group_id: int) -> list:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        raw_schedule = Schedule().get_raw_schedule(group_id)
        schedule = Schedule().process_schedule(raw_schedule, group_id)
        actual_data = [(None, *t) for i, t in enumerate(schedule)]
        with Session() as session:
            session.execute(insert(Schedule).values(actual_data))
            session.commit()
        return schedule

    def get_groups(self) -> list:
        """
        Вернёт лист, в котором будут находиться все ОСНОВНЫЕ группы(study_group)
        По которым следует искать расписания
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        groups_id = []
        with Session() as session:
            schedule_groups = session.query(Student.group_0).all()
        for group in schedule_groups:
            groups_id.append(group[0])
        return list(set(groups_id))  # Нужно, чтобы убрать дупликаты
            

    def get_new_lessons(self, groups_ids: list) -> None:
        """
        Функция выведет предметы, которые добавились в расписание
        :groups_ids: Лист, содержащий id каждой группы
        """
        raw_schedule = self.get_raw_schedule(groups_ids)
        group_schedule = self.process_schedule(raw_schedule)
        db_schedule = self.get_schedule_from_db()

        new_from_web = set(group_schedule) - set(db_schedule)
        deleted_from_web = set(db_schedule) - set(group_schedule)
        dont_tell_list  = []  # То, что нужно удалить, но не сообщать пользователю
        print(new_from_web)
        print(deleted_from_web)
        print(len(deleted_from_web))

        # Сначала нужен цикл, который 

        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        # Нужно фильтровать! Там где deleted_from_web, то если дата прошлая, то не отправлять сообщения

        # with Session() as session:
            # schedule = session.query(Schedule).filter_by(group_id=group_id).all()
            # print(schedule)


