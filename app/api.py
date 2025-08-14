import random

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.db.models import User, Wallet
from app.db.session import get_async_session
from app.schemas import SpinInput
from app.settings import settings

router = APIRouter(prefix='/api/v1')


@router.get('/utils/healthcheck')
async def healthcheck():
    return {'status': 'ok'}


@router.get('/users/{telegram_id}')
async def get_or_create_user(
    telegram_id: int,
    username: str = None,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.telegram_id == telegram_id))
    user = result.scalar_one_or_none()
    if not user:
        print(f'[DEBUG] Creating user with telegram_id: {telegram_id}')
        user = User(telegram_id=telegram_id, username=username, wallet=Wallet())
        session.add(user)
        await session.commit()
        await session.refresh(user)

    return {
        'user_id': user.id,
    }


@router.get('/users/info/{user_id}')
async def get_user(
        user_id: int,
        session: AsyncSession = Depends(get_async_session)
):
    query = select(User).where(User.id == user_id).options(selectinload(User.wallet))
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return {
        'user_id': user.id,
        'username': user.username,
        'balance': user.wallet.balance
    }


def make_spin() -> list[int]:
    return [0, 0, 0] if random.random() < 0.5 else [0, 1, 2]


def compute_multiplier(symbol_idxs: list[int]) -> float:
    if all(symbol == 0 for symbol in symbol_idxs):
        return settings.app.jackpot_multiplier
    else:
        return 0.


@router.post('/spin')
async def spin(
        spin: SpinInput,
        session: AsyncSession = Depends(get_async_session)
):
    user_id = spin.user_id
    bet = spin.bet

    query = select(Wallet.balance).where(Wallet.user_id == user_id)
    result = await session.execute(query)
    balance = result.scalar_one_or_none()

    if balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    if bet > balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Not enough balance')

    symbol_idxs = make_spin()
    multiplier = compute_multiplier(symbol_idxs)
    is_win = multiplier > 0
    updated_balance = balance - bet + bet * multiplier

    await session.execute(
        update(Wallet)
        .where(Wallet.user_id == user_id)
        .values(balance=updated_balance)
    )
    await session.commit()

    return {
        'is_win': is_win,
        'symbol_idxs': symbol_idxs,
    }

