from typing import Optional

from pydantic import BaseModel


class SessionIn(BaseModel):
    t: str


class SessionOut(BaseModel):
    tg_id: int
    username: Optional[str] = None
    user_id: Optional[int] = None
    jwt: str
    ctx: dict


class SpinIn(BaseModel):
    bet: int


class ScoreIn(BaseModel):
    score: int
