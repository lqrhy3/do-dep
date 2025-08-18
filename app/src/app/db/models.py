from sqlalchemy import Column, Integer, String, ForeignKey, CheckConstraint
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy.orm import relationship, validates

from app.settings import settings

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String, nullable=True)

    wallet = relationship(
        'Wallet',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
        passive_deletes=True,
    )


class Wallet(Base):
    __tablename__ = 'wallets'

    __table_args__ = (
        CheckConstraint('balance >= 0', name='ck_wallet_balance_nonnegative'),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True
    )
    user = relationship('User', back_populates='wallet')
    balance = Column(Integer, nullable=False, default=settings.app.initial_balance)

    @validates('balance')
    def _validate_balance(self, key, value):
        if value is not None and value < 0:
            raise ValueError('balance cannot be negative')
        return value
