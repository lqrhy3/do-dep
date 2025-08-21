import time
import jwt
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from aiogram import Bot

from app.db.models import User, Wallet
from app.db.session import get_async_db_session
from app.game_logic import compute_multiplier, make_spin
from app.schemas import ScoreIn, SessionIn, SessionOut, SpinIn
from app.settings import settings

router = APIRouter(prefix='/api/v1')


bot = Bot(settings.app.bot_token)


def _decode_api_session(authorization: Optional[str]):
    if not authorization or not authorization.startswith('Bearer '):
        return None
    token = authorization.split(' ', 1)[1]
    try:
        return jwt.decode(token, settings.app.api_jwt_secret, algorithms=['HS256'])
    except jwt.PyJWTError:
        return None


def _require_session(authorization: Optional[str]):
    session = _decode_api_session(authorization)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Missing or invalid authorization'
        )
    return session


@router.get('/utils/healthcheck')
async def healthcheck():
    return {'status': 'ok'}


@router.post('/session', response_model=SessionOut)
async def open_session(req: SessionIn, db_session: AsyncSession = Depends(get_async_db_session)):
    try:
        launch = jwt.decode(req.t, settings.app.jwt_secret, algorithms=['HS256'])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Launch token expired'
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid launch token'
        )

    tg_id = int(launch['uid'])
    username = launch.get('un')

    result = await db_session.execute(select(User).where(User.telegram_id == tg_id))
    user = result.scalar_one_or_none()
    if not user:
        user = User(telegram_id=tg_id, username=username, wallet=Wallet())
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
    elif username and user.username != username:
        user.username = username
        await db_session.commit()

    user_id = user.id
    query = select(Wallet.balance).where(Wallet.user_id == user_id)
    result = await db_session.execute(query)
    balance = result.scalar_one_or_none()

    ctx = {}
    if launch.get('inline_message_id'):
        ctx['inline_message_id'] = launch['inline_message_id']
    else:
        ctx['chat_id'] = launch.get('chat_id')
        ctx['message_id'] = launch.get('message_id')

    now = int(time.time())
    api_claims = {
        'sub': str(user.id),
        'tg_id': tg_id,
        'ctx': ctx,
        'iat': now,
        'exp': now + settings.app.api_jwt_ttl,
    }
    api_jwt = jwt.encode(api_claims, settings.app.api_jwt_secret, algorithm='HS256')

    return SessionOut(
        tg_id=tg_id,
        username=user.username,
        user_id=user.id,
        balance=balance,
        jwt=api_jwt,
        ctx=ctx
    )


@router.post('/spin')
async def spin_endpoint(
        req: SpinIn,
        authorization: str = Header(None),
        db_session: AsyncSession = Depends(get_async_db_session)
):
    session = _require_session(authorization)

    try:
        bet = int(req.bet)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Bet must be integer')
    if bet < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Bet must be positive')

    tg_id = int(session.get('tg_id'))
    result = await db_session.execute(select(User.id).where(User.telegram_id == tg_id))
    user_id = result.scalar_one_or_none()
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    query = select(Wallet.balance).where(Wallet.user_id == user_id)
    result = await db_session.execute(query)
    balance = result.scalar_one_or_none()
    if balance is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')
    if bet > balance:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Not enough balance')

    symbol_idxs = make_spin()
    multiplier = compute_multiplier(symbol_idxs)
    is_win = multiplier > 0
    updated_balance = balance - bet + bet * multiplier

    await db_session.execute(
        update(Wallet)
        .where(Wallet.user_id == user_id)
        .values(balance=updated_balance)
    )
    await db_session.commit()

    return {
        'is_win': is_win,
        'symbol_idxs': symbol_idxs,
        'balance': updated_balance
    }


@router.post('/score')
async def set_score(inp: ScoreIn, authorization: str = Header(None)):
    session = _require_session(authorization)
    if not bot:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Bot token not configured on API'
        )

    ctx = session.get('ctx') or {}
    if not ctx:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='No score context')

    kwargs = dict(
        user_id=int(session['tg_id']),
        score=int(inp.score),
        force=True,
        disable_edit_message=False
    )
    if ctx.get('inline_message_id'):
        kwargs['inline_message_id'] = ctx['inline_message_id']
    else:
        if not ctx.get('chat_id') or not ctx.get('message_id'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail='Incomplete score context'
            )
        kwargs['chat_id'] = ctx['chat_id']
        kwargs['message_id'] = ctx['message_id']

    await bot.set_game_score(**kwargs)
    return {'ok': True}
