import logging
from sqlalchemy import String, Boolean, BigInteger, select
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base, BaseModelWithTS, DbOperations, get_session
from config import config

logger = logging.getLogger(__name__)


class User(Base, BaseModelWithTS):
    __tablename__ = "user"

    telegram_id: Mapped[int] = mapped_column(
        BigInteger, index=True, unique=True, nullable=False
    )
    telegram_name: Mapped[str] = mapped_column(String(100), nullable=True)
    emby_name: Mapped[str] = mapped_column(String(50), nullable=True)
    emby_id: Mapped[str] = mapped_column(
        String(50), index=True, unique=True, nullable=True
    )
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_whitelist: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    enable_register: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    ban_time: Mapped[int] = mapped_column(nullable=True)
    reason: Mapped[str] = mapped_column(String(100), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<User(telegram_id={self.telegram_id}, "
            f"telegram_name={self.telegram_name}, "
            f"emby_name={self.emby_name}, "
            f"emby_id={self.emby_id}, "
            f"is_admin={self.is_admin}, "
            f"is_whitelist={self.is_whitelist}, "
            f"enable_register={self.enable_register}, "
            f"ban_time={self.ban_time})>"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def check_create_invite_code(self) -> bool:
        """判断当前用户是否能创建普通邀请码。"""
        return self.is_admin

    def check_create_whitelist_code(self) -> bool:
        """判断当前用户是否能创建白名单邀请码。"""
        return self.is_admin

    def check_emby_register(self) -> None:
        """检查是否允许用户创建 Emby 账号。"""
        if not self.enable_register:
            raise Exception("您当前无权限创建 Emby 账号。")
        if self.emby_id is not None:
            raise Exception("该用户已拥有 Emby 账号，无法重复创建。")

    def check_use_redeem_code(self) -> None:
        """检查是否可使用普通注册邀请码。"""
        if self.emby_id is not None:
            raise Exception("该用户已拥有 Emby 账号，无法再次使用注册邀请码。")
        if self.enable_register:
            raise Exception("该用户已经具备创建 Emby 账号的资格，无需再次使用邀请码。")

    def check_use_whitelist_code(self) -> None:
        """检查是否可使用白名单邀请码。"""
        if self.emby_id is None:
            raise Exception("该用户尚未拥有 Emby 账号，无法使用白名单邀请码。")
        if self.is_whitelist:
            raise Exception("该用户已在白名单，无需再次使用。")

    def check_emby_ban(self) -> None:
        """检查是否可对该用户进行 Emby 禁用。"""
        if not self.has_emby_account():
            raise Exception("该用户尚未绑定 Emby 账号，无法禁用。")
        if self.is_emby_baned():
            raise Exception("该用户的 Emby 账号已被禁用，无需重复操作。")

    def check_emby_unban(self) -> None:
        """检查是否可对该用户进行 Emby 账号解禁。"""
        if not self.has_emby_account():
            raise Exception("该用户尚未绑定 Emby 账号，无法执行解禁。")
        if not self.is_emby_baned():
            raise Exception("该用户的 Emby 账号当前未被禁用，无需解禁。")

    def check_set_emby_config(self) -> None:
        """检查是否可修改 Emby 全局配置（仅管理员可操作）"""
        if not self.is_bot_admin():
            raise Exception("您没有管理员权限，无法修改 Emby 全局配置。")

    def is_bot_admin(self) -> bool:
        """判断当前用户是否是 Bot 管理员（由 config.admin_list 控制）"""
        return self.telegram_id in config.admin_list

    def has_emby_account(self) -> bool:
        """判断当前用户是否已经绑定了 Emby 账号。"""
        return self.emby_id is not None

    def is_emby_baned(self) -> bool:
        """判断当前 Emby 账号是否已被禁用（ban_time > 0)"""
        return self.ban_time and self.ban_time > 0

    def emby_ban_info(self) -> tuple[int, str]:
        """返回该用户被 ban 的时间戳与原因，用于外部查询。"""
        return self.ban_time, self.reason


class UserRepository:
    """Replaces UserOrm to handle User database operations"""

    @staticmethod
    async def create_user(**kwargs):
        return await DbOperations.create(User, **kwargs)

    @staticmethod
    async def get_by_id(user_id: int):
        return await DbOperations.get_by_id(User, user_id)

    @staticmethod
    async def get_by_telegram_id(telegram_id: int):
        async for session in get_session():
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalars().first()

    @staticmethod
    async def get_by_emby_id(emby_id: str):
        async for session in get_session():
            result = await session.execute(select(User).where(User.emby_id == emby_id))
            return result.scalars().first()

    @staticmethod
    async def update_user(user_id: int, **kwargs):
        return await DbOperations.update(User, user_id, **kwargs)

    @staticmethod
    async def delete_user(user_id: int):
        return await DbOperations.delete(User, user_id)
