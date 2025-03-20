import logging
from sqlalchemy import Integer, BigInteger, select
from sqlalchemy.orm import mapped_column, Mapped

from .database import Base, BaseModelWithTS, DbOperations, get_session
from .invite_code_model import InviteCode

logger = logging.getLogger(__name__)


class Config(Base, BaseModelWithTS):
    __tablename__ = "config"

    total_register_user: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    register_public_user: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    register_public_time: Mapped[int] = mapped_column(BigInteger, nullable=True)


class ConfigRepository:
    """Replaces ConfigOrm to handle Config database operations"""

    @staticmethod
    async def create_config(**kwargs):
        return await DbOperations.create(Config, **kwargs)

    @staticmethod
    async def get_by_id(config_id: int):
        return await DbOperations.get_by_id(Config, config_id)

    @staticmethod
    async def get_first_config():
        """Get the first (and typically only) config record"""
        async for session in get_session():
            result = await session.execute(select(Config).limit(1))
            return result.scalars().first()

    @staticmethod
    async def update_config(config_id: int, **kwargs):
        return await DbOperations.update(Config, config_id, **kwargs)

    @staticmethod
    async def create_invite_code(**kwargs):
        return await DbOperations.create(InviteCode, **kwargs)

    # @staticmethod
    # async def get_by_id(code_id: int):
    #     return await DbOperations.get_by_id(InviteCode, code_id)

    @staticmethod
    async def get_by_code(code: str):
        async for session in get_session():
            result = await session.execute(
                select(InviteCode).where(InviteCode.code == code)
            )
            return result.scalars().first()

    @staticmethod
    async def get_by_telegram_id(telegram_id: int):
        async for session in get_session():
            result = await session.execute(
                select(InviteCode).where(InviteCode.telegram_id == telegram_id)
            )
            return result.scalars().all()

    @staticmethod
    async def update_invite_code(code_id: int, **kwargs):
        return await DbOperations.update(InviteCode, code_id, **kwargs)

    @staticmethod
    async def mark_as_used(code_id: int, used_time: int, used_user_id: int):
        return await DbOperations.update(
            InviteCode,
            code_id,
            is_used=True,
            used_time=used_time,
            used_user_id=used_user_id,
        )
