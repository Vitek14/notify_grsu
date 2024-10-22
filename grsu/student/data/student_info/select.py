from sqlalchemy import select
from sqlalchemy.orm import Session, Mapped


class SelectInfoMixin:
    tg_id: Mapped[str]

    def get_all_info(self, tg_id: int) -> dict[str, str | int]:
        """
        Получит всю базовую информацию о студенте, включая ФИО, Курс, группу и т.д...
        :param tg_id: Telegram ID пользователя, для которого получить информацию.
        :return: Словарь со всей базовой информацией из str/int
        """
        with Session() as session:
            class_params = [getattr(self, column.name) for column in self.__table__.columns]
            result = session.execute(select(*class_params).where(self.tg_id == tg_id)).first()._asdict()

        return result

    def get_info(self, search: list[str], tg_id: int) -> dict[str, str | int]:
        """
        Получит некоторую(указанную) базовую информацию о студенте.
        :param search: Лист из полей класса, которые добавлять в результат поиска.
        :param tg_id: Telegram ID пользователя, для которого получить информацию.
        :return: Словарь с базовой информацией
        """
        with Session() as session:
            search_info = [getattr(self, attr) for attr in search]  # Добавляем self в аргументы
            result = session.execute(select(*search_info)
                                     .where(self.tg_id == tg_id)).first()._asdict()

        return result
