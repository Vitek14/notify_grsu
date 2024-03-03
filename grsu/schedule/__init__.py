from requests import delete
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update, insert, select
import datetime  # Для проверки даты(что неделя уже не прошла)

from datetime import datetime, timedelta
from grsu import student

from grsu.student import Student
from grsu.student.settings import Settings

Base = declarative_base()
student = Student()
settings = Settings()

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

    def get_student_schedule_from_db(self, group_id):
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
            Schedule.end_time, Schedule.group_id, Schedule.subgroup_id).where(group_id==group_id)).all()
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
            

    def get_new_lessons(self, groups_ids: list):
        """
        Функция выведет предметы, которые добавились в расписание
        :groups_ids: Лист, содержащий id каждой группы
        """
        raw_schedule = self.get_raw_schedule(groups_ids)
        group_schedule = self.process_schedule(raw_schedule)
        db_schedule = self.get_schedule_from_db()

        new_from_web = set(group_schedule) - set(db_schedule)
        deleted_from_web = set(db_schedule) - set(group_schedule)
        new_notify = []
        deleted_notify = []

        dont_notify = []

        two_weeks_ago = datetime.today() - timedelta(weeks=2)
        if len(new_from_web) > 0:
            for lesson in new_from_web:
                date = datetime.strptime(lesson[5], "%Y-%m-%d")
                if date > two_weeks_ago:
                    new_notify.append(lesson)
                else:
                    dont_notify.append(lesson)

        if len(deleted_from_web) > 0:
            for lesson in deleted_from_web:
                date = datetime.strptime(lesson[5], "%Y-%m-%d")
                if date > two_weeks_ago:
                    deleted_notify.append(lesson)
                else:
                    dont_notify.append(lesson)

        return new_notify, deleted_notify, dont_notify
        # ДАЛЬШЕ ДЕЛАТЬ ФУНКЦИИ ВСТАВКИ, УДАЛЕНИЯ И ОПОВЕЩЕНИЯ ПОЛЬЗОВАТЕЛЯ


        # Сначала нужен цикл, который 

    def update_db(self, new_notify, deleted_notify, dont_notify) -> None:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        # Нужно фильтровать! Там где deleted_from_web, то если дата прошлая, то не отправлять сообщения

        with Session() as session:
            if len(new_notify) > 0:
                actual_data = [(None, *t) for i, t in enumerate(new_notify)]
                session.execute(insert(Schedule).values(actual_data)) # type: ignore
            # Объединяем 2 листа, которые нужно удалить
            if len(deleted_notify) > 0 or len(dont_notify) > 0:
                deletable = deleted_notify + dont_notify
                for lesson in deletable:
                    session.query(Schedule).filter_by(name=lesson[0], date=lesson[5], group_id=lesson[9]).delete()
            session.commit()


    def get_schedule_text(self, lessons: list, student_groups: list, is_notify: bool) -> list:
        """
        Вернёт лист с текстом расписания и id студента, которому должно быть отправлено этот текст
        :lessons: Расписание из базы данных или API
        :student_groups: Все студенты
        :is_notify: Если этот должно быть отправлено как оповещение
        """
        student_notification = []

        # Сортировка по времени
        lessons = sorted(lessons, key=lambda x: x[7])

        # Для каждого студента перебираем
        for student in student_groups:
            user_settings = settings.get_settings(student[6])
            print(student)
            lab_groups = student[1:5]
            print("LAB GROUPS: " + str(lab_groups))
            all_lessons = ""

            # Для каждого урока
            for lesson in lessons:
                # Если студент есть в той группе, в которой должно быть отправлено уведомление, то вот проверка
                if lesson[9] == student[0] or lesson[10] in lab_groups:
                    if "УСР" in lesson[1].upper() and user_settings["show_USR"] == 0:
                            continue
                    if "ФАКУЛЬТАТИВ" in lesson[1].upper() and user_settings["show_facultative"] == 0:
                        continue
                        
                        # Если студента нет в этой группе, то переходить к след занятию
                    if lesson[10] and not lesson[10] in lab_groups:
                        continue

                    if not is_notify and lesson[5] != student[7]:
                        continue
                        
                    # Лист в котором хранится все данные об уроке, кроме его названия
                    elements = []
                    text_lessons = "<b>" + lesson[0] + "</b>. "
                    if user_settings["show_lesson_type"] == 1:
                        elements.append(lesson[1])
                    if user_settings["show_adress"] == 1:
                        elements.append(lesson[2])
                    if user_settings["show_room"] == 1:
                        elements.append(lesson[3])
                    if user_settings["show_teacher"] == 1:
                        elements.append(lesson[4])
                    if user_settings["show_full_data"] == 1:
                        elements.append(lesson[5])
                    if user_settings["show_start_time"] == 1:
                        elements.append(str(lesson[7]))
                    if user_settings["show_end_time"] == 1:
                        elements.append(str(lesson[8]))
                    if is_notify:
                        current_date = datetime.strptime(lesson[5], "%Y-%m-%d")
                        # strftime("%A, %d %b
                        text_date = current_date.strftime(" (%A, %d %b.)")
                        elements.append(text_date)

                    
                    # Перевести лист elements в строковый тип, разделяя данные с помощью ", "
                    normal_lessons = ", ".join(elements)
                    all_lessons = all_lessons + text_lessons + normal_lessons + "\n"
            student_notification.append(
                {
                    "text": all_lessons,
                    "id": student[6]
                }
            )
            return student_notification


    async def notify(self, bot) -> None:
        groups_ids = self.get_groups()
        new_notify, deleted_notify, dont_notify = self.get_new_lessons(groups_ids)
        self.update_db(new_notify, deleted_notify, dont_notify)

        student_groups = student.get_groups_all()
        new_notify_text = self.get_schedule_text(new_notify, student_groups, True)
        deleted_notify_text = self.get_schedule_text(deleted_notify, student_groups, True)
        for text in new_notify_text:
            if len(text["text"]) == 0:
                continue
            await bot.send_message(text["id"], "Добавлено:\n" + text["text"], parse_mode="HTML")
        for text in deleted_notify_text:
            if len(text["text"]) == 0:
                continue
            await bot.send_message(text["id"], "Удалено:\n" + text["text"], parse_mode="HTML")
