from loguru import logger
from requests import delete
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy import update, insert, select
from io import BytesIO
import PIL
from PIL import Image, ImageDraw, ImageFont

import datetime  # Для проверки даты(что неделя уже не прошла)

from datetime import datetime, timedelta
from grsu import student

from grsu.student import Student
from grsu.student.settings import Settings

from ..exceptions import ScheduleNotFound

Base = declarative_base()
student = Student()
settings = Settings()


class Schedule(Base):
    """Класс расписания определяет общее расписание студентов, а также их домашние задания"""
    __tablename__ = "schedule"
    rowid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str]
    lesson_type: Mapped[str]
    place: Mapped[str]
    room: Mapped[str]
    teacher: Mapped[str]
    date: Mapped[str]
    day: Mapped[int]
    start_time: Mapped[str]
    end_time: Mapped[str]
    group_id: Mapped[int]
    subgroup_id: Mapped[int]
    homework: Mapped[str]
    homework_added_by_id: Mapped[int]

    @staticmethod
    def if_exists(group_id: int) -> bool:
        """
        Функция проверяет существование расписания для группы.
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

    @staticmethod
    def get_schedule_from_db() -> list:
        """
        Функция выдаёт всё расписание по группе.
        :group_id: ID группы, для которого искать расписание
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
            # schedule = session.query(Schedule).filter_by(Schedule.group_id=group_id).all()
            schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
                                              Schedule.place, Schedule.room, Schedule.teacher, Schedule.date,
                                              Schedule.day, Schedule.start_time,
                                              Schedule.end_time, Schedule.group_id, Schedule.subgroup_id)).all()
        return schedule

    @staticmethod
    def get_student_schedule_from_db(group_id: int, date: str | None = None) -> list:
        """
        Функция выдаёт всё расписание по группе.
        :param group_id: ID группы, для которой искать расписание.
        :param date: Дата, за которую искать расписание(None, если искать за всё время)
        :return: Лист из кортежей со всеми занятиями за дату/все занятия
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
            if not date:
                logger.trace("Дата не указана, возвращаем всё расписание")
                schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
                                                  Schedule.place, Schedule.room, Schedule.teacher, Schedule.date,
                                                  Schedule.day, Schedule.start_time,
                                                  Schedule.end_time, Schedule.group_id, Schedule.subgroup_id).
                                           where(Schedule.group_id == group_id)).all()
            else:
                logger.trace(f"Поиск по дате: {date}")
                schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
                                                  Schedule.place, Schedule.room, Schedule.teacher, Schedule.date,
                                                  Schedule.day, Schedule.start_time,
                                                  Schedule.end_time, Schedule.group_id, Schedule.subgroup_id).
                                           where(Schedule.group_id == group_id, Schedule.date == date)).all()
            logger.debug(f"Расписание: {schedule}")
        return schedule

    @staticmethod
    def create_schedule(groups_ids: list) -> None:
        """
        Создаст расписание для указанных групп.
        :param groups_ids: Лист групп студента, включая основную и лабораторные.
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        raw_schedule = Schedule().get_raw_schedule(groups_ids)
        schedule = Schedule().process_schedule(raw_schedule)
        if not schedule:
            raise ScheduleNotFound
        actual_data = [(None, *t) for i, t in enumerate(schedule)]
        with Session() as session:
            session.execute(insert(Schedule).values(actual_data))
            session.commit()

    @staticmethod
    def get_groups() -> list:
        """
        :return: Вернёт лист, в котором будут находиться все ОСНОВНЫЕ группы(study_group) студентов
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
        return list(set(groups_id))  # Нужно, чтобы убрать дубликаты

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
                session.execute(insert(Schedule).values(actual_data))  # type: ignore
            # Объединяем 2 листа, которые нужно удалить
            if len(deleted_notify) > 0 or len(dont_notify) > 0:
                deletable = deleted_notify + dont_notify
                for lesson in deletable:
                    session.query(Schedule).filter_by(name=lesson[0], date=lesson[5], group_id=lesson[9]).delete()
            session.commit()

    @staticmethod
    def get_schedule_raw_image(lessons) -> Image.Image:
        """
        Делает стандартную картинку расписания с заданным кол-во занятий
        """

        # Открываем исходное изображение
        im = Image.open("grsu/schedule/images/schedule.png")

        # Задаем координаты для вырезаемой области
        left = 0
        top = 0
        right = 1072
        lesson_pixels = 195
        bottom = 2000 - (8 - lessons) * lesson_pixels

        # Вырезаем область из исходного изображения
        im1 = im.crop((left, top, right, bottom))

        # Открываем второе изображение, которое хотим вставить

        im2 = Image.open("grsu/schedule/images/border.png")

        # Вставляем второе изображение в вырезанную область
        im1.paste(im2, (left, bottom - 126))

        # # Показываем итоговое изображение
        # im1.show()
        return im1

    @staticmethod
    def get_schedule_text(lessons: list, student_groups: list, is_notify: bool) -> list:
        """
        Вернёт лист с текстом расписания и id студента, которому должно быть отправлено этот текст.
        :lessons: Расписание из базы данных или API
        :student_groups: Все студенты.
        :is_notify: Если этот должно быть отправлено как оповещение
        """
        student_notification = []

        # Сортировка по времени
        lessons = sorted(lessons, key=lambda x: x[7])

        # Для каждого студента перебираем
        for _student in student_groups:
            logger.debug(f"_student is: {_student}")
            user_settings = settings.get_settings(_student[6])
            lab_groups = _student[1:5]
            print("LAB GROUPS: " + str(lab_groups))
            all_lessons = ""

            # Для каждого урока
            real_lessons = 0
            for lesson in lessons:
                logger.debug(f"Lesson: {lesson}")

                if not is_notify and lesson[5] != _student[7]:
                    logger.trace(f"Пропущено занятие: {lesson}. is_notify={is_notify}, date={_student[7]}")
                    continue

                # Если студент есть в той группе, в которой должно быть отправлено уведомление, то вот проверка
                if lesson[9] == _student[0] or lesson[10] in lab_groups:
                    if "УСР" in lesson[1].upper() and user_settings["show_USR"] == 0:
                        continue
                    if "ФАКУЛЬТАТИВ" in lesson[1].upper() and user_settings["show_facultative"] == 0:
                        continue

                    # Если студента нет в этой группе, то переходить к след занятию
                    if lesson[10] and not lesson[10] in lab_groups:
                        continue

                    # Лист в котором хранится все данные об уроке, кроме его названия
                    elements = []
                    text_lessons = "<b>" + lesson[0] + "</b>. "
                    if user_settings["show_lesson_type"] == 1:
                        elements.append(lesson[1])
                    if user_settings["show_address"] == 1:
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

                    real_lessons += 1  # Увеличиваем кол-во занятий для картинки. Нельзя использовать len(lessons),
                    # т.к возможно пользователь выбрал не показывать УСР

            student_notification.append(
                {
                    "text": all_lessons,
                    "id": _student[6],
                    "real_lessons": real_lessons
                }
            )

            return student_notification

    def get_schedule_photo(self, student_param: tuple, lessons: list, real_lessons: int, current_day: datetime.date):
        """
        Функция создаст фото с расписанием текущего дня
        """
        logger.trace(f"В get_schedule_photo передан student_param как: {student_param}")
        raw_image = self.get_schedule_raw_image(real_lessons)

        # Взять настройки студента по его id
        user_settings = settings.get_settings(student_param[6])

        draw = ImageDraw.Draw(raw_image)

        # specified font size 
        font = ImageFont.truetype("grsu/schedule/images/Prosto_Sans_Bold.otf", 24)

        # TODO: Изменить, чтобы не рисовало не только сегодняшний день
        date = current_day.strftime("%d.%m.%Y")

        # drawing text size 
        draw.text((715 + 103, 174), date, fill=(0, 0, 0, 255), font=font, align="left", anchor="ma")

        datetime_font = ImageFont.truetype("grsu/schedule/images/OpenSans-Bold.ttf", 24)
        lesson_name_font = ImageFont.truetype("grsu/schedule/images/OpenSans-Bold.ttf", 28)
        lesson_text = ImageFont.truetype("grsu/schedule/images/OpenSans-Regular.ttf", 24)

        lesson_name_px = 267
        lesson_name_py = 384

        lesson_type_py = 424

        lesson_time_py = 454

        lesson_room_px = 140
        lesson_room_py = 420
        lab_groups = student_param[1:5]
        for lesson in lessons:
            logger.debug(f"Занятие: {lesson}")
            # Если студент есть в той группе, в которой должно быть отправлено уведомление, то вот проверка
            if lesson[9] == student_param[0] or lesson[10] in lab_groups:
                if "УСР" in lesson[1].upper() and user_settings["show_USR"] == 0:
                    continue
                if "ФАКУЛЬТАТИВ" in lesson[1].upper() and user_settings["show_facultative"] == 0:
                    continue

                    # Если студента нет в этой группе, то переходить к след занятию
                if lesson[10] and not lesson[10] in lab_groups:
                    continue

                # Лист в котором хранится все данные об уроке, кроме его названия
                # elements = []
                # text_lessons = "<b>" + lesson[0] + "</b>. "
                if len(lesson[0]) > 35:
                    draw.text((lesson_name_px, lesson_name_py), lesson[0][:36]+"...", fill="#ee6664", font=lesson_name_font,
                              align="left")
                else:
                    draw.text((lesson_name_px, lesson_name_py), lesson[0], fill="#ee6664", font=lesson_name_font,
                          align="left")

                # elements.append(lesson[1])  # Тип занятия

                first_line_text = lesson[1] + ", " + lesson[2]
                second_line_text = str(lesson[7]) + " - " + str(lesson[8])

                draw.text((lesson_name_px, lesson_type_py), first_line_text, fill="black", font=lesson_text)
                draw.text((lesson_name_px, lesson_time_py), second_line_text, fill="black", font=lesson_text)
                if len(lesson[3]) < 4:
                    draw.text((lesson_room_px, lesson_room_py), lesson[3], fill="black", font=datetime_font,
                              align="left")
                else:
                    draw.text((lesson_room_px, lesson_room_py), "...", fill="black", font=datetime_font, align="left")

                lesson_name_py += 194
                lesson_time_py += 194
                lesson_room_py += 194
                lesson_type_py += 194
                bio = BytesIO()
                bio.name = 'schedule.png'
                raw_image.save(bio, 'png')
                bio.seek(0)
                # bytes_image = bytes(raw_image.tobytes())

                # if raw_image.tobytes() == bytes_image:
                #     print("ALL GOOD")
                # else:
                #     print("bad.....")
        return bio

    async def notify(self, bot) -> None:
        logger.info("Отрабатывает функция оповещения")
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
