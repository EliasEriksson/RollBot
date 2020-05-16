from .db import Users, DATABASE_ADDRESS, create_database, ENGINE
from .errors import *
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


class Manager:
    def __init__(self, engine=DATABASE_ADDRESS):
        self.engine = create_engine(engine)
        session = sessionmaker()
        session.configure(bind=self.engine)
        self.session = session()

    async def __aenter__(self):
        return self.open()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @classmethod
    async def open(cls):
        instance = cls()
        if not instance.engine.dialect.has_table(ENGINE, Users.__tablename__):
            create_database()
        return instance

    async def close(self):
        self.session.close()

    async def add_user(self, user_id: int, wallet: int = 100) -> None:
        user = self.session.query(Users).filter(Users.user_id == user_id).first()
        if user:
            raise UserAlreadyExists()
        user = Users(user_id=user_id, wallet=wallet)
        self.session.add(user)
        self.session.commit()

    async def get_users_wallet(self, user_id: int) -> int:
        user: Users = self.session.query(Users).filter(Users.user_id == user_id).first()
        if not user:
            raise UserDoesNotExist
        return user.wallet

    async def give_money(self, sender_id: int, receiver_id: int, amount: int) -> None:
        sender: Users = self.session.query(Users).filter(Users.user_id == sender_id).first()
        if not sender:
            raise SenderDoesNotExist()
        if not sender.wallet >= amount:
            raise NotEnoughMoney()
        receiver: Users = self.session.query(Users).filter(Users.user_id == receiver_id).first()
        if not receiver:
            raise ReceiverDoesNotExist()
        sender.wallet -= amount
        receiver.wallet += amount
        self.session.commit()

    async def add_welfare(self, *user_ids: int, amount: int = 11):
        for user_id in user_ids:
            user: Users = self.session.query(Users).filter(Users.user_id == user_id).first()
            if user:
                user.wallet += amount
        self.session.commit()

    async def acquire_tax(self, *user_ids: int, tax: float = 0.045):
        for user_id in user_ids:
            user: Users = self.session.query(Users).filter(Users.user_id == user_id).first()
            if user:
                user.wallet = int(user.wallet * (100 - tax))
        self.session.commit()
