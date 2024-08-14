from sqlalchemy import Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Mapped, mapped_column
from sqlalchemy import create_engine
from sqlalchemy import update

Base = declarative_base()
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)
Session = sessionmaker(engine)


class Settings(Base):
    """Класс настроек студента"""
    __tablename__ = "user_preferences"
    rowid: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int]
    show_today_at_end: Mapped[int] = mapped_column(nullable=False, default=1)
    auto_login: Mapped[int] = mapped_column(nullable=False, default=1)
    auto_time: Mapped[int] = mapped_column(nullable=False, default=1)
    show_faculty: Mapped[int] = mapped_column(nullable=False, default=1)
    show_specialization: Mapped[int] = mapped_column(nullable=False, default=1)
    show_email: Mapped[int] = mapped_column(nullable=False, default=1)
    show_group: Mapped[int] = mapped_column(nullable=False, default=1)
    send_marks_notification: Mapped[int] = mapped_column(nullable=False, default=1)
    send_schedule_notification: Mapped[int] = mapped_column(nullable=False, default=1)
    send_homework_notification: Mapped[int] = mapped_column(nullable=False, default=1)
    send_update_notification: Mapped[int] = mapped_column(nullable=False, default=1)
    show_USR: Mapped[int] = mapped_column(nullable=False, default=1)
    show_address: Mapped[int] = mapped_column(nullable=False, default=1)
    show_room: Mapped[int] = mapped_column(nullable=False, default=1)
    show_teacher: Mapped[int] = mapped_column(nullable=False, default=1)
    show_full_data: Mapped[int] = mapped_column(nullable=False, default=1)
    show_start_time: Mapped[int] = mapped_column(nullable=False, default=1)
    show_end_time: Mapped[int] = mapped_column(nullable=False, default=1)
    show_facultative: Mapped[int] = mapped_column(nullable=False, default=1)
    show_lesson_type: Mapped[int] = mapped_column(nullable=False, default=1)

    @staticmethod
    def create_settings(user_id: int) -> None:
        with Session() as session:
            settings = Settings(rowid=None, user_id=user_id)
            session.add(settings)
            session.commit()

    @staticmethod
    def get_settings(user_id: int) -> dict:
        """Получит все настройки пользователя"""
        with Session() as session:
            settings = session.query(Settings).filter_by(user_id=user_id).first()
            if not settings:
                return {}
            else:
                return settings.__dict__

    @staticmethod
    def update_setting(user_id: int, setting_name: str, value: int) -> None:
        """Обновит настройку пользователя"""
        with Session() as session:
            update_values = {setting_name: value}
            session.execute(update(Settings).where(Settings.user_id == user_id).values(**update_values))
            # update(Settings).where(auto_time==user_id).values(setting_name=value)
            session.commit()
