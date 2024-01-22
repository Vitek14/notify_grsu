from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import delete

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)

# Объявляем объект сессии
Session = sessionmaker(engine)

def delete_marks(self, user_id: int, data) -> None:
    Marks = self.__class__
    with Session() as session:
        session.execute(delete(Marks).values(data)) # type: ignore
        session.commit()
