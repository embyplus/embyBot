import logging
import enum
from py_tools.connections.db.mysql import DBManager
from py_tools.connections.db.mysql.orm_model import BaseOrmTableWithTS
from sqlalchemy import String, BigInteger, Boolean, Enum
from sqlalchemy.orm import Mapped, mapped_column

logger = logging.getLogger(__name__)


class InviteCodeType(enum.Enum):
    REGISTER = "register"  # 注册邀请码
    WHITELIST = "whitelist"  # 白名单邀请码

    def __str__(self):
        return self.value


class InviteCode(BaseOrmTableWithTS):
    __tablename__ = "invite_code"

    code: Mapped[str] = mapped_column(
        String(50), index=True, unique=True, nullable=False
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, index=True, nullable=False
    )
    code_type: Mapped[InviteCodeType] = mapped_column(
        Enum(InviteCodeType), nullable=False
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    used_time: Mapped[int] = mapped_column(
        BigInteger, default=None, nullable=True
    )
    used_user_id: Mapped[int] = mapped_column(
        BigInteger, default=None, nullable=True, index=True
    )

    def __repr__(self):
        return (
            f"<InviteCode(code={self.code}, telegram_id={self.telegram_id}, "
            f"code_type={self.code_type}, is_used={self.is_used}, "
            f"used_time={self.used_time}, used_user_id={self.used_user_id})>"
        )


class InviteCodeOrm(DBManager):
    orm_table = InviteCode


logger.info("InviteCode model initialized")
