from aiogram import Router, F
from aiogram.types import Message, InlineQuery, InlineQueryResultGame, InlineKeyboardButton, \
    InlineKeyboardMarkup, CallbackQuery, CallbackGame

import time
import logging
import jwt
from aiogram.filters import Command

from app.settings import settings

logger = logging.getLogger(__name__)
router = Router()


def _build_launch_token(cb: CallbackQuery) -> str:
    payload = {
        'uid': cb.from_user.id,
        'un': cb.from_user.username or 'Guest',
        'inline_message_id': cb.inline_message_id,
        'chat_id': cb.message.chat.id if cb.message else None,
        'message_id': cb.message.message_id if cb.message else None,
        'iat': int(time.time()),
        'exp': int(time.time()) + 10 * 60,
    }
    return jwt.encode(payload, settings.app.jwt_secret, algorithm='HS256')


async def _send_game(msg: Message):
    markup = InlineKeyboardMarkup(
        inline_keyboard=[[
            InlineKeyboardButton(
                text='▶ Play',
                callback_game=CallbackGame()
            )
        ]]
    )
    await msg.answer_game(settings.app.game_short_name, reply_markup=markup)


@router.inline_query()
async def inline_query_handler(query: InlineQuery):
    await query.answer(
        results=[InlineQueryResultGame(id='1', game_short_name=settings.app.game_short_name)],
        cache_time=0
    )


@router.callback_query(F.game_short_name == settings.app.game_short_name)
async def game_callback_handler(callback_query: CallbackQuery):
    token = _build_launch_token(callback_query)
    url = f'{settings.app.game_url}?t={token}'
    logger.info('Opening game URL: %s', url)
    await callback_query.answer(url=url)


@router.message(Command('start'))
async def start_command(msg: Message):
    await _send_game(msg)


@router.message(Command('play'))
async def play_command(msg: Message):
    await _send_game(msg)

