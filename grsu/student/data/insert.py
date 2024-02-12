from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import insert

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)

# Объявляем объект сессии
Session = sessionmaker(engine)

def insert_new_marks(self, user_id: int, data: list) -> None:
    Marks = self.__class__
    with Session() as session:
        actual_data = [(None, *t) for i, t in enumerate(data)]
        session.execute(insert(Marks).values(actual_data)) # type: ignore
        session.commit()