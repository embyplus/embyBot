import logging
import enum
from sqlalchemy import String, BigInteger, Boolean, Enum, select
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, BaseModelWithTS, DbOperations, get_session

logger = logging.getLogger(__name__)


class InviteCodeType(enum.Enum):
    REGISTER = "register"  # 注册邀请码
    WHITELIST = "whitelist"  # 白名单邀请码

    def __str__(self):
        return self.value


class InviteCode(Base, BaseModelWithTS):
    __tablename__ = "invite_code"

    code: Mapped[str] = mapped_column(
        String(50), index=True, unique=True, nullable=False
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True, nullable=False)
    code_type: Mapped[InviteCodeType] = mapped_column(
        Enum(InviteCodeType), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    used_time: Mapped[int] = mapped_column(BigInteger, default=None, nullable=True)
    used_user_id: Mapped[int] = mapped_column(
        BigInteger, default=None, nullable=True, index=True
    )

    def __repr__(self):
        return (
            f"<InviteCode(code={self.code}, telegram_id={self.telegram_id}, "
            f"code_type={self.code_type}, is_used={self.is_used}, "
            f"used_time={self.used_time}, used_user_id={self.used_user_id})>"
        )


class InviteCodeRepository:
    """Replaces InviteCodeOrm to handle InviteCode database operations"""

    @staticmethod
    async def create_invite_code(**kwargs):
        return await DbOperations.create(InviteCode, **kwargs)

    @staticmethod
    async def get_by_id(code_id: int):
        return await DbOperations.get_by_id(InviteCode, code_id)

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
