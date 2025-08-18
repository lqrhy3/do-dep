from contextlib import asynccontextmanager

from app.settings import settings
from aiogram import Bot
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bot = Bot(settings.app.bot_token)
    try:
        yield
    finally:
        await app.state.bot.session.close()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)
app.include_router(router)
