import asyncio
import os
import logging
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select, update, text
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.models import User, Wallet, WalletTransaction
from app.db.session import AsyncSessionLocal
from app.settings import settings


LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s %(levelname)s %(name)s: %(message)s',
)
logger = logging.getLogger('refill.worker')


BATCH_SIZE = 5000


def current_bucket_start(
        now: datetime | None = None,
        bucket_hours: int = settings.worker.bucket_hours
) -> datetime:
    if now is None:
        now = datetime.now(timezone.utc)
    secs = int(now.timestamp())
    size = bucket_hours * 3600
    floored = secs - (secs % size)
    return datetime.fromtimestamp(floored, tz=timezone.utc)


def chunked(iterable: Iterable[int], size: int):
    buf = []
    for x in iterable:
        buf.append(x)
        if len(buf) >= size:
            yield buf
            buf = []
    if buf:
        yield buf


async def process_chunk(
        session,
        user_ids: list[int],
        window_start: datetime,
        amount: int,
        reason: str
) -> int:
    if not user_ids:
        return 0

    t = WalletTransaction.__table__
    ins = (
        pg_insert(t)
        .values([
            {'user_id': uid, 'amount': amount, 'reason': reason, 'window_start': window_start}
            for uid in user_ids
        ])
        .on_conflict_do_nothing(index_elements=['user_id', 'window_start', 'reason'])
        .returning(t.c.user_id)
    )

    res = await session.execute(ins)
    inserted_user_ids = res.scalars().all()
    if not inserted_user_ids:
        return 0

    await session.execute(
        update(Wallet)
        .where(Wallet.user_id.in_(inserted_user_ids))
        .values(balance=Wallet.balance + amount)
        .execution_options(synchronize_session=False)
    )
    logger.debug(f'batch credited users={len(inserted_user_ids)} amount={amount}')
    return len(inserted_user_ids)


async def refill_all_users():
    window_start = current_bucket_start()
    credited_total = 0
    window_iso = window_start.isoformat()

    async with AsyncSessionLocal() as session:
        got_res = await session.execute(
            text('SELECT pg_try_advisory_lock(:k)'), {'k': settings.worker.lock_key}
        )
        got = got_res.scalar()
        if not got:
            logger.debug(f'skip tick: lock not acquired (window={window_iso})')
            return 0
        logger.debug(f'lock acquired (window={window_iso})')

        try:
            stream = await session.stream_scalars(select(User.id).order_by(User.id))
            batch: list[int] = []
            async for uid in stream:
                batch.append(uid)
                if len(batch) >= BATCH_SIZE:
                    credited_total += await process_chunk(
                        session=session,
                        user_ids=batch,
                        window_start=window_start,
                        amount=settings.worker.refill_amount,
                        reason='periodic_refill'
                    )
                    batch = []
            if batch:
                credited_total += await process_chunk(
                    session=session,
                    user_ids=batch,
                    window_start=window_start,
                    amount=settings.worker.refill_amount,
                    reason='periodic_refill'
                )

            await session.commit()
            logger.info(f'refill committed: credited={credited_total} window={window_iso}')
            return credited_total
        except Exception:
            logger.exception(f'refill failed (window={window_iso})')
            await session.rollback()
            raise
        finally:
            await session.execute(
                text('SELECT pg_advisory_unlock(:k)'), {'k': settings.worker.lock_key}
            )
            logger.debug(f'lock released (window={window_iso})')


async def main_loop():
    logger.info(
        'refill worker started: amount=%s bucket_hours=%s tick_seconds=%s batch_size=%s',
        settings.worker.refill_amount,
        settings.worker.bucket_hours,
        settings.worker.tick_seconds,
        BATCH_SIZE,
    )
    while True:
        try:
            credited = await refill_all_users()
            logger.debug('tick done: credited=%s', credited)
        except Exception:
            logger.exception('tick error')
        finally:
            await asyncio.sleep(settings.worker.tick_seconds)


if __name__ == '__main__':
    asyncio.run(main_loop())
