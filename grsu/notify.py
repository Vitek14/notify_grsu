import asyncio

from aiohttp import ClientSession  # Странно работает, переход на httpx
import httpx
from loguru import logger
from grsu.schedule import Schedule
from grsu.student import Student
from grsu.student.marks import Marks
# from asyncio import loo

schedule = Schedule()
student = Student()
marks = Marks()


async def process_student(id: int):
    pass


async def notify() -> None:
    """
    Асинхронная функция уведомления. Пробежится по каждому зарегистрированному пользователю(параллельно) и будет
    сравнивать полученное расписание из базы данных с новым.
    :return: None
    """
    async with httpx.AsyncClient() as client:
        logger.info("Отрабатывает асинхронная функция оповещения")
        groups_ids = schedule.get_groups()
        # Будем получать новые занятия для каждой группы!!
        first_tasks = []  # Задачи с расписанием и логином, которые пустим в асинхронность
        for group in groups_ids:
            schedule_task = asyncio.create_task(
                    schedule.async_get_raw_schedule(group, client), name="raw_schedule"
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
                        client
                    ), name="login_task"
                )
                first_tasks.append(login_task)

        student_tasks = []
        while first_tasks:
            done, pending = await asyncio.wait(
                first_tasks, return_when=asyncio.FIRST_COMPLETED
            )
            for task in done:
                logger.info(f"Выполнена асинхронная задача: {task.get_name()}")
                if task.get_name() == "raw_schedule":
                    result = await task
                    logger.debug(f"TASK RESULT: {result}")
                    group_id = task.group_id
                    db_schedule = schedule.get_schedule_from_db(group_id=group_id)
                    # new_lessons, deleted_lessons, real_deleted_lessons = self.get_api_changes(group)
                if task.get_name() == "login_task":
                    result = await task

                    # Теперь выполняем основные запросы со студентом
                    student_tasks.append(
                        asyncio.create_task(
                            student.async_about(result, client), name="about"
                        )
                    )
                    student_tasks.append(
                        asyncio.create_task(
                            student.async_get_skips(result, client), name="skips"
                        )
                    )
                    student_tasks.append(
                        asyncio.create_task(
                            student.async_get_exams(result, client), name="get_exams"
                        )
                    )
                    student_tasks.append(
                        asyncio.create_task(
                            student.async_get_attestation(result, client), name="get_attestation"
                        )
                    )
                    student_tasks.append(
                        asyncio.create_task(
                            marks.async_get_courses_names(result, client)
                        )
                    )
                    while student_tasks:  # Переделать?
                        done_student, pending_student = await asyncio.wait(
                            student_tasks, return_when=asyncio.FIRST_COMPLETED
                        )
                        for student_task in done_student:
                            st_task = await student_task
                            logger.info(f"Выполнена асинхронная задача: {student_task.get_name()}")
                        student_tasks = list(pending_student)
                    logger.debug(f"TASK RESULT: {result}")

                first_tasks = list(pending)
    # logger.debug(f"DONE: {done}")
