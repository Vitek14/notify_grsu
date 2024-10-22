from typing import Tuple, List, Any, Dict, Set

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
from ._web import AsyncWebScheduleMixin

from ..exceptions import ScheduleNotFound
import time
from pprint import pformat

Base = declarative_base()
student = Student()
settings = Settings()


class Schedule(Base, AsyncWebScheduleMixin):
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
    def get_schedule_from_db(group_id: int | None = None) -> list:
        """
        Функция найдёт все расписание/расписание по группе.
        :param group_id: (Необязательно)ID study_group, чтобы искать по нему.
        :return: Лист с расписанием из базы данных
        """
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        # Объявляем объект сессии
        Session = sessionmaker(engine)
        with Session() as session:
            # schedule = session.query(Schedule).filter_by(Schedule.group_id=group_id).all()
            if not group_id:
                schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
                                                  Schedule.place, Schedule.room, Schedule.teacher, Schedule.date,
                                                  Schedule.day, Schedule.start_time,
                                                  Schedule.end_time, Schedule.group_id, Schedule.subgroup_id)).all()
            else:
                logger.trace(f"")
                schedule = session.execute(select(Schedule.name, Schedule.lesson_type,
                                                  Schedule.place, Schedule.room, Schedule.teacher, Schedule.date,
                                                  Schedule.day, Schedule.start_time,
                                                  Schedule.end_time, Schedule.group_id,
                                                  Schedule.subgroup_id).where(Schedule.group_id == group_id)).all()
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

    @staticmethod
    def process_new_lessons(new_lessons: list[tuple], db_schedule: list[tuple]) -> tuple[
        list[tuple], list[dict], list[tuple]
    ]:
        """
        Обработает 'новые занятия' на правда новые и изменённые.
        :param db_schedule: Расписание из базы данных.
        :param new_lessons: Лист, содержащий все потенциально новые занятия в виде кортежей.
        :return: Переменные с новыми занятиями, изменёнными, а также занятия, которые уже ненужны.
        """
        real_new_lessons = []
        changed_lessons = []
        very_old_lessons = []

        two_weeks_ago = datetime.today() - timedelta(weeks=2)

        # Цикл для каждого занятия. Сверяем что именно добавилось.
        for lesson in new_lessons:
            logger.trace(f"Обработка: {lesson}")
            lesson_date = datetime.strptime(f"{lesson[5]}.{lesson[7]}", "%Y-%m-%d.%H:%M")
            logger.trace(f"Обработанная дата занятия: {lesson_date}")
            is_added_lesson = True  # Обозначает, является ли занятие новым в расписании или изменённым
            if lesson_date > two_weeks_ago:  # TODO: Проверить
                for old_lesson in db_schedule:
                    logger.trace(f"Old_lesson: {old_lesson}")
                    logger.trace(f"New lesson: {lesson}")
                    notify_add = {}
                    if old_lesson[0] == lesson[0] and old_lesson[5] == lesson[5] and old_lesson[7] == lesson[7]:
                        # ВОЗМОЖНО в будущем добавить также сравнение по id группы.
                        logger.info(f"Изменение в {lesson[0]} на {lesson[5]}")
                        is_added_lesson = False
                        notify_add["name"] = lesson[0]
                        if old_lesson[1] != lesson[1]:
                            notify_add["lesson_type"] = lesson[1]
                        if old_lesson[2] != lesson[2]:
                            notify_add["place"] = lesson[2]
                        if old_lesson[3] != lesson[3]:
                            notify_add["room"] = lesson[3]
                        if old_lesson[4] != lesson[4]:
                            notify_add["teacher"] = lesson[4]
                        if old_lesson[7] != lesson[7]:
                            notify_add["start_time"] = lesson[7]
                        if old_lesson[8] != lesson[8]:
                            notify_add["end_time"] = lesson[8]
                        # Дальше время начала и конца, но нам это неважно
                        # notify_add["date"] = lesson[5]
                        notify_add["date"] = lesson[5] + "." + lesson[7]
                        notify_add["group_id"] = lesson[9]
                        notify_add["subgroup_id"] = lesson[10]
                        logger.debug(notify_add)
                        changed_lessons.append(notify_add)
                if is_added_lesson:
                    real_new_lessons.append(lesson)
            else:
                very_old_lessons.append(lesson)

        return real_new_lessons, changed_lessons, very_old_lessons

    def get_api_changes(self, group: int) -> tuple[
        list[tuple] | set[Any], list[tuple] | set[Any], list[tuple[str, str, str, str]] | set
    ]:
        """
        Функция вернёт лист со словарями, в которых имеются сведения о конкретных изменениях.
        :param group: ID study_group.
        :return: Лист из словарей, в которых содержатся сведения об изменениях.
        """
        logger.info("Получение новых занятий(get_new_lessons)")
        tic = time.perf_counter()
        raw_schedule = self.get_raw_schedule([group])
        toc = time.perf_counter()
        logger.trace(f"Расписание взято из API за {toc - tic:0.4f}")
        group_schedule = self.process_schedule(raw_schedule)

        db_schedule = self.get_schedule_from_db(group_id=group)

        logger.trace(f"group_schedule: {group_schedule}")
        logger.trace(f"db_schedule: {db_schedule}")

        new_from_web = set(group_schedule) - set(db_schedule)  # TODO: Возможно добавить штуку,
        # чтобы была ГРУППИРОВКА по одинаковым изменениям?
        logger.debug(pformat(new_from_web))

        deleted_from_web = set(db_schedule) - set(group_schedule)

        # Далее получаем что действительно было удалено из расписания
        basic_group_schedule: list[tuple[str, str, str, str]] = [
            (item[0], item[5], item[7], item[8]) for item in group_schedule
        ]
        basic_db_schedule: list[tuple[str, str, str, str]] = [
            (item[0], item[5], item[7], item[8])for item in db_schedule
        ]
        real_deleted_from_web = set(basic_db_schedule) - set(basic_group_schedule)

        logger.debug(f"Новое из API: {new_from_web}")
        logger.debug(f"Удалено из API: {deleted_from_web}")
        if len(deleted_from_web) == 0:
            deleted_from_web = []
        return new_from_web, deleted_from_web, real_deleted_from_web

    @staticmethod
    def update_db(new_notify, deleted_notify, very_old_lessons) -> None:
        engine = create_engine('sqlite:///user.db')
        Base.metadata.create_all(engine)
        Session = sessionmaker(engine)

        with Session() as session:
            if len(new_notify) > 0:
                actual_data = [(None, *t) for i, t in enumerate(new_notify)]
                session.execute(insert(Schedule).values(actual_data))  # type: ignore
            # Объединяем 2 листа, которые нужно удалить
            if len(deleted_notify) > 0 or len(very_old_lessons) > 0:
                deletable = list(deleted_notify) + very_old_lessons
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
    def get_human_date(date: datetime, compare_date: datetime) -> str:
        """
        Превратит дату в нормальную читабельную строку.
        :param date: Исходная дата.
        :param compare_date: Дата, с которой нужно сравнивать.
        :return: Строка(Завтра/Послезавтра/Вчера/...)
        """
        human_date = date.strftime("%A")
        logger.debug(f"Date.day is {date.day} and compare_date.day is {compare_date.day}")
        logger.trace(f"+1: {(date + timedelta(days=1)).day}; {(compare_date + timedelta(days=1)).day}")
        if date.day == compare_date.day:
            human_date = "Сегодня"
        if date.day == (compare_date + timedelta(days=1)).day:
            human_date = "Завтра"
        if date.day == (compare_date + timedelta(days=2)).day:
            human_date = "Послезавтра"
        if date.day == (compare_date - timedelta(days=1)).day:
            human_date = "Вчера"
        if date.day == (compare_date - timedelta(days=2)).day:
            human_date = "Позавчера"
        return human_date

    def get_provided_lessons_text(
            self, provided_lessons: list[tuple], max_date: datetime, min_date: datetime, provider="NEW"
    ) -> str:
        """
        Сделает текст для новых занятий.
        :param provider: Указатель какие занятия предоставлены. ВОЗМОЖНЫЕ ВАРИАНТЫ: NEW и DELETED.
        :param min_date: Дата, до которой оповещать не нужно.
        :param max_date: Дата, после которой оповещать не нужно.
        :param provided_lessons: Лист из кортежей, в которых хранится информация о новых занятиях.
        :return: Текст оповещения о новых занятий.
        """
        text = ""
        date = datetime.today()

        if provider == "NEW":
            text = "Добавлено в расписание:\n"
        elif provider == "DELETED":
            text = "Удалено из расписания:\n"
        else:
            logger.error(f"Параметр provider может быть только NEW или DELETED. Предоставлено: {provider}")
        for lesson in provided_lessons:
            if provider == "NEW":
                date = datetime.strptime(f"{lesson[5]}.{lesson[7]}", "%Y-%m-%d.%H:%M")
            elif provider == "DELETED":
                date = datetime.strptime(f"{lesson[1]}.{lesson[2]}", "%Y-%m-%d.%H:%M")
            human_date = self.get_human_date(date, datetime.today())
            if date > max_date or date < min_date:
                logger.trace(f"Пропущено занятие({lesson})")
                continue
            if provider == "NEW":
                text += f"{lesson[0]} - {human_date} в {lesson[7]}\n"
            elif provider == "DELETED":
                text += f"{lesson[0]} - {human_date}\n"
            logger.debug(f"text в new_lessons: {text}")
        return text

    def get_changed_schedule_text(self, changed_lessons: list[dict[str, str | int | datetime]],
                                  max_date: datetime, min_date: datetime) -> str:
        text = "Изменения в расписании:\n"
        for lesson in changed_lessons:
            date = datetime.strptime(lesson["date"], "%Y-%m-%d.%H:%M")
            human_date = self.get_human_date(date, datetime.today())  # TODO: ПРОВЕРИТЬ
            logger.debug(f"Полученная дата в человеческом формате: {human_date}")
            logger.trace(f"Переменные date и max_date и min_date: {date}; {max_date}; {min_date}")
            if date > max_date or date < min_date:
                logger.trace(f"Пропущено занятие({lesson})")
                continue
            logger.debug(f"Обработка 'get_changed_schedule_text для {lesson}'")
            text += f"{lesson['name']}({human_date})\n"
            for ch_key, ch_v in lesson.items():
                if ch_key == "lesson_type":
                    text += f"  Тип занятия изменён на {ch_v}\n"
                if ch_key == "place":
                    text += f"  Адрес изменён на {ch_v}\n"
                if ch_key == "room":
                    text += f"  Аудитория изменена на {ch_v}\n"
                if ch_key == "teacher":
                    text += f"  Сменился преподаватель на {ch_v}\n"
        logger.debug(text)
        return text

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
        lessons = sorted(lessons, key=lambda x: x[7])
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
                    draw.text((lesson_name_px, lesson_name_py), lesson[0][:36] + "...", fill="#ee6664",
                              font=lesson_name_font,
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
        tic = time.perf_counter()
        # Будем получать новые занятия для каждой группы!!
        for group in groups_ids:
            db_schedule = self.get_schedule_from_db(group_id=group)
            new_lessons, deleted_lessons, real_deleted_lessons = self.get_api_changes(group)
            if (len(new_lessons) and real_deleted_lessons) == 0:
                logger.info(f"Изменений для {group} нет.")
                continue

            groups_info = student.get_students_with_group(group)
            for student_group in groups_info:
                notify_text = ""
                st_settings = settings.get_settings(student_group[6])
                logger.debug(f"Получены настройки для telegram id {student_group[6]}: {st_settings}")
                max_date_notify = datetime.today() + timedelta(days=st_settings["days_notify"])
                back_days_notify = datetime.today() - timedelta(days=st_settings["back_days_notify"])
                if len(new_lessons) > 0:  # Значит, что изменения точно существуют и их нужно обработать
                    logger.debug(f"NEW LESSONS: {new_lessons}")
                    real_new_lessons, changed_lessons, very_old_lessons = self.process_new_lessons(new_lessons,
                                                                                                   db_schedule)
                    if len(changed_lessons) > 0:
                        changed_lessons_text = self.get_changed_schedule_text(changed_lessons, max_date_notify,
                                                                              back_days_notify)
                        notify_text += changed_lessons_text
                    if len(real_new_lessons) > 0:
                        new_lessons_text = self.get_provided_lessons_text(
                            new_lessons, max_date_notify, back_days_notify
                        )
                        notify_text += new_lessons_text
                    if len(real_deleted_lessons) > 0:
                        new_lessons_text = self.get_provided_lessons_text(
                            real_deleted_lessons, max_date_notify, back_days_notify, provider="DELETED"
                        )
                        notify_text += new_lessons_text
                    await bot.send_message(student_group[6], notify_text)
                    self.update_db(new_lessons, deleted_lessons, very_old_lessons)
