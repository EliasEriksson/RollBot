from sqlalchemy import create_engine
from sqlalchemy import Column, Integer
from sqlalchemy.ext.declarative import declarative_base
from pathlib import Path


PROJECT_ROOT = Path(__file__).absolute().parent.parent
DATABASE_ADDRESS = f"sqlite:////{str(PROJECT_ROOT.joinpath('db.db'))}"
ENGINE = create_engine(DATABASE_ADDRESS)
Base = declarative_base()


class Users(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True)
    wallet = Column(Integer)

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @classmethod
    def create(cls, engine):
        cls.metadata.create_all(engine)

    def __repr__(self):
        return f"{self.__tablename__}(id={self.id}, user={self.user_id}, wallet={self.wallet})"


def create_database():
    Users.create(ENGINE)


if __name__ == '__main__':
    Users.create(ENGINE)
