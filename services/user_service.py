import logging
import re
import string
from datetime import datetime
from random import sample
from typing import Optional, List, Dict, Tuple

import shortuuid

from config import config
from core.emby_api import EmbyApi, EmbyRouterAPI
from models.config_model import Config, ConfigRepository
from models.invite_code_model import InviteCode, InviteCodeRepository, InviteCodeType
from models.user_model import User, UserRepository
from models.database import get_session

logger = logging.getLogger(__name__)


class NotBoundError(Exception):
    """用户未绑定 Emby 账号的异常"""

    pass


class UserService:
    """用户与 Emby 相关的业务逻辑层"""

    def __init__(self, emby_api: EmbyApi, emby_router_api: EmbyRouterAPI):
        self.emby_api = emby_api
        self.emby_router_api = emby_router_api

    @staticmethod
    async def get_or_create_user_by_telegram_id(telegram_id: int) -> User:
        """通过 telegram_id 从数据库获取用户，如果不存在则创建一个默认用户"""
        user = await UserRepository.get_by_telegram_id(telegram_id)
        if not user:
            # Create new user with parameters instead of User object
            user = await UserRepository.create_user(
                telegram_id=telegram_id,
                is_admin=telegram_id in config.admin_list,
                telegram_name=config.group_members.get(telegram_id, {}).username
                if config.group_members.get(telegram_id)
                else None,
            )
        return user

    @staticmethod
    async def is_admin(telegram_id: int) -> bool:
        """判断指定的 Telegram 用户是否为管理员"""
        user = await UserService.get_or_create_user_by_telegram_id(telegram_id)
        return user and user.is_admin

    async def must_get_user(self, telegram_id: int) -> User:
        """获取指定用户信息，不存在则抛出异常"""
        user = await self.get_or_create_user_by_telegram_id(telegram_id)
        if user is None:
            raise Exception("未找到该用户的信息。")
        return user

    async def must_get_emby_user(self, telegram_id: int) -> User:
        """确保用户存在且已创建 Emby 账号，若不存在则抛出异常"""
        user = await self.must_get_user(telegram_id)
        if user.emby_id is None:
            raise Exception("该用户尚未绑定 Emby 账号，无法执行此操作。")
        if user.ban_time is not None and user.ban_time > 0:
            raise Exception("该用户的 Emby 账号已被禁用，无法执行此操作。")
        return user

    async def _emby_create_user(
        self, telegram_id: int, username: str, password: str
    ) -> User:
        """内部使用：真正调用 Emby API 创建用户，并设置初始密码"""
        user = await self.get_or_create_user_by_telegram_id(telegram_id)
        emby_user = self.emby_api.create_user(username)
        if not emby_user or not emby_user.get("Id"):
            raise Exception("在 Emby 系统中创建账号失败，请检查 Emby 服务是否正常。")

        emby_id = emby_user["Id"]
        # Update user directly with UserRepository
        await UserRepository.update_user(
            user.id, emby_id=emby_id, emby_name=username, enable_register=False
        )

        # Reload user after update
        user = await UserRepository.get_by_id(user.id)

        # 设置初始密码 & 默认Policy
        self.emby_api.set_user_password(emby_id, password)
        self.emby_api.set_default_policy(emby_id)
        return user

    @staticmethod
    def gen_default_passwd() -> str:
        """生成默认密码：随机6位的字母数字组合"""
        return "".join(sample(string.ascii_letters + string.digits, 6))

    @staticmethod
    def gen_register_code(num: int) -> List[str]:
        """批量生成普通邀请码"""
        return [f"epr-{str(shortuuid.uuid())}" for _ in range(num)]

    @staticmethod
    def gen_whitelist_code(num: int) -> List[str]:
        """批量生成白名单邀请码"""
        return [f"epw-{str(shortuuid.uuid())}" for _ in range(num)]

    async def create_invite_code(
        self, telegram_id: int, count: int = 1
    ) -> List[InviteCode]:
        """创建普通邀请码，需检测用户是否有权限"""
        user = await self.must_get_user(telegram_id)
        if not user.check_create_invite_code():
            raise Exception("您没有权限生成普通邀请码。")

        # Create and store invite codes one by one
        created_codes = []
        for code in self.gen_register_code(count):
            invite_code = await InviteCodeRepository.create_invite_code(
                code=code, telegram_id=telegram_id, code_type=InviteCodeType.REGISTER
            )
            created_codes.append(invite_code)

        return created_codes

    async def create_whitelist_code(
        self, telegram_id: int, count: int = 1
    ) -> List[InviteCode]:
        """创建白名单邀请码，需检测用户是否有权限"""
        user = await self.must_get_user(telegram_id)
        if not user.check_create_whitelist_code():
            raise Exception("您没有权限生成白名单邀请码。")

        # Create and store whitelist codes one by one
        created_codes = []
        for code in self.gen_whitelist_code(count):
            invite_code = await InviteCodeRepository.create_invite_code(
                code=code, telegram_id=telegram_id, code_type=InviteCodeType.WHITELIST
            )
            created_codes.append(invite_code)

        return created_codes

    async def emby_info(self, telegram_id: int) -> Tuple[User, Dict]:
        """获取当前用户在 Emby 的信息"""
        user = await self.must_get_user(telegram_id)
        if not user.has_emby_account():
            raise NotBoundError("该用户尚未绑定 Emby 账号。")
        emby_user = self.emby_api.get_user(str(user.emby_id))
        if not emby_user:
            raise Exception(
                "从 Emby 服务器获取用户信息失败，请检查 Emby 服务是否正常。"
            )
        return user, emby_user

    async def first_or_create_emby_config(self) -> Config:
        """获取或创建 Emby 配置。"""
        emby_config = await ConfigRepository.get_by_id(1)
        if not emby_config:
            emby_config = await ConfigRepository.create_config(
                register_public_user=0, register_public_time=0, total_register_user=0
            )
        return emby_config

    async def emby_create_user(
        self, telegram_id: int, username: str, password: str
    ) -> User:
        """创建 Emby 用户（外部调用入口），先判断各种配置是否允许注册，然后调用内部的 _emby_create_user"""
        user = await self.get_or_create_user_by_telegram_id(telegram_id)
        if user.has_emby_account():
            raise Exception("该 Telegram 用户已经绑定过 Emby 账号，无法重复创建。")

        emby_config = await self.first_or_create_emby_config()
        if not emby_config:
            raise Exception("未找到 Emby 配置，无法创建账号。")

        if not await self._check_register_permission(user, emby_config):
            raise Exception("当前没有可用的注册权限或名额，创建账号被拒绝。")

        # Use manual session management instead of transaction context manager
        async for session in get_session():
            try:
                if not user.enable_register and emby_config.register_public_user > 0:
                    emby_config.register_public_user -= 1

                emby_config.total_register_user += 1
                await ConfigRepository.update_config(
                    emby_config.id,
                    register_public_user=emby_config.register_public_user,
                    total_register_user=emby_config.total_register_user,
                )

                # Create user in Emby system
                new_user = await self._emby_create_user(telegram_id, username, password)

                await session.commit()
                return new_user
            except Exception as e:
                await session.rollback()
                logger.error(f"创建用户失败: {e}")
                raise

    async def _check_register_permission(self, user: User, emby_config: Config) -> bool:
        """检查用户是否有权限注册 Emby 账号"""
        enable_register = user.enable_register
        if not enable_register and emby_config.register_public_user > 0:
            enable_register = True
        if (
            not enable_register
            and emby_config.register_public_time > 0
            and datetime.now().timestamp() < emby_config.register_public_time
        ):
            enable_register = True
        if 0 < emby_config.register_public_time < datetime.now().timestamp():
            await ConfigRepository.update_config(1, register_public_time=0)
        return enable_register

    async def redeem_code(self, telegram_id: int, code: str):
        """使用邀请码，分为普通注册邀请码和白名单邀请码"""
        pattern = re.compile(r"^(epr|epw)-[A-Za-z0-9]+$")
        if not pattern.match(code):
            raise Exception("邀请码格式不正确。")

        user = await self.must_get_user(telegram_id)

        # Use direct session rather than transaction context manager
        async for session in get_session():
            try:
                # Get invite code
                valid_code = await InviteCodeRepository.get_by_code(code)

                if not valid_code or valid_code.is_used:
                    raise Exception("该邀请码无效或已被使用。")

                # 根据邀请码类型执行不同的业务逻辑校验
                if valid_code.code_type == InviteCodeType.REGISTER:
                    user.check_use_redeem_code()
                elif valid_code.code_type == InviteCodeType.WHITELIST:
                    user.check_use_whitelist_code()
                    if user.is_emby_baned():
                        await self.emby_unban(telegram_id)

                # Mark code as used
                now = int(datetime.now().timestamp())
                await InviteCodeRepository.mark_as_used(valid_code.id, now, telegram_id)

                # Update user based on code type
                if valid_code.code_type == InviteCodeType.REGISTER:
                    await UserRepository.update_user(user.id, enable_register=True)
                elif valid_code.code_type == InviteCodeType.WHITELIST:
                    await UserRepository.update_user(user.id, is_whitelist=True)

                await session.commit()

                # Refresh user object after update
                user = await UserRepository.get_by_id(user.id)
                return valid_code
            except Exception as e:
                await session.rollback()
                logger.error(f"使用邀请码失败: {e}")
                raise

    async def reset_password(self, telegram_id: int, password: str = "") -> bool:
        """重置用户的 Emby 密码。"""
        user = await self.must_get_emby_user(telegram_id)
        try:
            self.emby_api.reset_user_password(user.emby_id)
            self.emby_api.set_user_password(user.emby_id, password)
            return True
        except Exception as e:
            logger.error(f"重置密码失败: {e}")
            return False

    async def emby_ban(
        self, telegram_id: int, reason: str, operator_telegram_id: Optional[int] = None
    ) -> bool:
        """禁用用户"""
        if operator_telegram_id is not None:
            admin_user = await self.must_get_user(operator_telegram_id)
            if not admin_user.is_admin:
                raise Exception("您没有管理员权限，无法执行禁用操作。")

        user = await self.must_get_user(telegram_id)
        user.check_emby_ban()

        try:
            self.emby_api.ban_user(str(user.emby_id))
            ban_time = int(datetime.now().timestamp())
            await UserRepository.update_user(user.id, ban_time=ban_time, reason=reason)
            return True
        except Exception as e:
            logger.error(f"禁用用户失败: {e}")
            return False

    async def emby_unban(
        self, telegram_id: int, operator_telegram_id: Optional[int] = None
    ) -> bool:
        """解禁用户"""
        if operator_telegram_id is not None:
            admin_user = await self.must_get_user(operator_telegram_id)
            if not admin_user.is_admin:
                raise Exception("您没有管理员权限，无法执行解禁操作。")

        user = await self.must_get_user(telegram_id)
        user.check_emby_unban()

        try:
            self.emby_api.set_default_policy(str(user.emby_id))
            await UserRepository.update_user(user.id, ban_time=0, reason=None)
            return True
        except Exception as e:
            logger.error(f"解禁用户失败: {e}")
            return False

    async def set_emby_config(
        self,
        telegram_id: int,
        register_public_user: Optional[int] = None,
        register_public_time: Optional[int] = None,
    ) -> Config:
        """设置 Emby 注册相关配置，如公共注册名额和公共注册截止时间"""
        user = await self.must_get_user(telegram_id)
        user.check_set_emby_config()

        emby_config = await self.first_or_create_emby_config()
        if not emby_config:
            raise Exception("未找到全局 Emby 配置，无法设置。")

        update_data = {}
        if register_public_user is not None:
            update_data["register_public_user"] = register_public_user
        if register_public_time is not None:
            update_data["register_public_time"] = register_public_time

        if update_data:
            await ConfigRepository.update_config(emby_config.id, **update_data)
            # Refresh config after update
            emby_config = await ConfigRepository.get_by_id(emby_config.id)

        return emby_config

    def emby_count(self) -> Dict:
        """从 Emby API 获取当前影片数量统计"""
        return self.emby_api.count()

    async def get_user_router(self, telegram_id: int) -> Dict:
        """获取用户的线路信息"""
        user = await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.query_user_route(user.emby_id)

    async def update_user_router(self, telegram_id: int, new_index: str) -> bool:
        """更新用户线路信息"""
        user = await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.update_user_route(str(user.emby_id), str(new_index))

    async def get_router_list(self, telegram_id: int) -> List[Dict]:
        """获取所有可用线路"""
        await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.query_all_route()
