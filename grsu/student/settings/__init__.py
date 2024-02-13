from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy import update

Base = declarative_base()
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)
Session = sessionmaker(engine)


class Settings(Base):
    """Класс настроек студента"""
    __tablename__ = "user_preferences"
    rowid = Column("rowid", Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    show_today_at_end = Column(Integer, nullable=False, default=1)
    auto_login = Column(Integer, nullable=False, default=1)
    auto_time = Column(Integer, nullable=False, default=1)
    show_faculty = Column(Integer, nullable=False, default=1)
    show_specialization = Column(Integer, nullable=False, default=1)
    show_email = Column(Integer, nullable=False, default=1)
    show_group = Column(Integer, nullable=False, default=1)
    send_marks_notification = Column(Integer, nullable=False, default=1)
    send_schedule_notification = Column(Integer, nullable=False, default=1)
    send_homework_notification = Column(Integer, nullable=False, default=1)
    send_update_notification = Column(Integer, nullable=False, default=1)
    show_USR = Column(Integer, nullable=False, default=1)
    show_adress = Column(Integer, nullable=False, default=1)
    show_room = Column(Integer, nullable=False, default=1)
    show_teacher = Column(Integer, nullable=False, default=1)
    show_full_data = Column(Integer, nullable=False, default=1)
    show_start_time = Column(Integer, nullable=False, default=1)
    show_end_time = Column(Integer, nullable=False, default=1)
    show_facultative = Column(Integer, nullable=False, default=1)
    show_lesson_type = Column(Integer, nullable=False, default=1)

    def create_settings(self, user_id: int) -> None:
        with Session() as session:
            settings = Settings(rowid=None, user_id=user_id)
            session.add(settings)
            session.commit()

    def get_settings(self, user_id: int) -> dict:
        """Получит все настройки пользователя"""
        with Session() as session:
            settings = session.query(Settings).filter_by(user_id=user_id).first()
            if not settings:
                return {}
            else:
                return settings.__dict__

    def update_setting(self, user_id: int, setting_name: str, value: int) -> None:
        """Обновит настройку пользователя"""
        with Session() as session:
            update_values = {setting_name: value}
            session.execute(update(Settings).where(Settings.user_id == user_id).values(**update_values))
            # update(Settings).where(auto_time==user_id).values(setting_name=value)
            session.commit()

