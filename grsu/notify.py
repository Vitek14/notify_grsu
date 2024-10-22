import asyncio

from aiohttp import ClientSession
from loguru import logger
from grsu.schedule import Schedule
from grsu.student import Student
# from asyncio import loo

schedule = Schedule()
student = Student()


async def process_student(id: int):
    pass


async def notify(session: ClientSession) -> None:
    """
    Асинхронная функция уведомления. Пробежится по каждому зарегистрированному пользователю(параллельно) и будет
    сравнивать полученное расписание из базы данных с новым.
    :return: None
    """
    logger.info("Отрабатывает асинхронная функция оповещения")
    groups_ids = schedule.get_groups()
    # Будем получать новые занятия для каждой группы!!
    first_tasks = []  # Задачи с расписанием и логином, которые пустим в асинхронность
    for group in groups_ids:
        schedule_task = asyncio.create_task(
                schedule.async_get_raw_schedule(group, session), name="raw_schedule"
            )
        schedule_task.group_id = group
        # first_tasks.append()
        first_tasks.append(schedule_task)
        groups_info = student.get_students_with_group(group)
        for student_group in groups_info:
            login = student.get_login(student_group[6])
            login_task = asyncio.create_task(
                student.async_auth(
                    login["username"],
                    login["password"],
                    session
                ), name="login_task"
            )
            first_tasks.append(login_task)

    while first_tasks:
        loop = asyncio.get_event_loop()
        done, first_tasks = loop.run_until_complete(asyncio.wait(
            first_tasks, return_when=asyncio.FIRST_COMPLETED
        ))
        for task in done:
            logger.info(f"Выполнена асинхронная задача: {task.get_name()}")
            logger.debug("Может возникнуть далее ошибка из-за .get_name(), что странно")
            if task.get_name() == "raw_schedule":
                result = await task
                group_id = task.group_id
                db_schedule = schedule.get_schedule_from_db(group_id=group_id)
                # new_lessons, deleted_lessons, real_deleted_lessons = self.get_api_changes(group)
