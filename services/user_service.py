import logging
import re
import string
from datetime import datetime
from random import sample
from typing import Optional, List, Dict, Tuple

import shortuuid
from sqlalchemy import select

from config import config
from core.emby_api import EmbyApi, EmbyRouterAPI
from models import User, Config, InviteCode
from models.config_model import ConfigOrm
from models.invite_code_model import InviteCodeOrm, InviteCodeType
from models.user_model import UserOrm

logger = logging.getLogger(__name__)


class UserService:
    """用户与 Emby 相关的业务逻辑层"""

    def __init__(self, emby_api: EmbyApi, emby_router_api: EmbyRouterAPI):
        self.emby_api = emby_api
        self.emby_router_api = emby_router_api

    @staticmethod
    async def get_or_create_user_by_telegram_id(telegram_id: int) -> User:
        """通过 telegram_id 从数据库获取用户，如果不存在则创建一个默认用户"""
        user = await UserOrm().query_one(
            conds=[User.telegram_id == telegram_id]
        )
        if not user:
            default_user = User(
                telegram_id=telegram_id,
                is_admin=telegram_id in config.admin_list,
                telegram_name=config.group_members.get(
                    telegram_id, {}
                ).username
                if config.group_members.get(telegram_id)
                else None,
            )
            user_id = await UserOrm().add(default_user)
            user = default_user
            user.id = user_id
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
            raise Exception(
                "在 Emby 系统中创建账号失败，请检查 Emby 服务是否正常。"
            )

        emby_id = emby_user["Id"]
        user.emby_id = emby_id
        user.emby_name = username
        user.enable_register = False

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

        code_objs = [
            InviteCode(
                code=code,
                telegram_id=telegram_id,
                code_type=InviteCodeType.REGISTER,
            )
            for code in self.gen_register_code(count)
        ]
        return await InviteCodeOrm().bulk_add(code_objs)

    async def create_whitelist_code(
        self, telegram_id: int, count: int = 1
    ) -> List[InviteCode]:
        """创建白名单邀请码，需检测用户是否有权限"""
        user = await self.must_get_user(telegram_id)
        if not user.check_create_whitelist_code():
            raise Exception("您没有权限生成白名单邀请码。")

        code_objs = [
            InviteCode(
                code=code,
                telegram_id=telegram_id,
                code_type=InviteCodeType.WHITELIST,
            )
            for code in self.gen_whitelist_code(count)
        ]
        return await InviteCodeOrm().bulk_add(code_objs)

    async def emby_info(self, telegram_id: int) -> Tuple[User, Dict]:
        """获取当前用户在 Emby 的信息"""
        user = await self.must_get_user(telegram_id)
        if not user.has_emby_account():
            raise Exception("该用户尚未绑定 Emby 账号。")
        emby_user = self.emby_api.get_user(str(user.emby_id))
        if not emby_user:
            raise Exception(
                "从 Emby 服务器获取用户信息失败，请检查 Emby 服务是否正常。"
            )
        return user, emby_user

    async def first_or_create_emby_config(self) -> Config:
        """获取或创建 Emby 配置。"""
        emby_config = await ConfigOrm().query_one(conds=[Config.id == 1])
        if not emby_config:
            emby_config = Config(
                register_public_user=0,
                register_public_time=0,
                total_register_user=0,
            )
            await ConfigOrm().add(emby_config)
        return emby_config

    async def emby_create_user(
        self, telegram_id: int, username: str, password: str
    ) -> User:
        """创建 Emby 用户（外部调用入口），先判断各种配置是否允许注册，然后调用内部的 _emby_create_user"""
        user = await self.get_or_create_user_by_telegram_id(telegram_id)
        if user.has_emby_account():
            raise Exception(
                "该 Telegram 用户已经绑定过 Emby 账号，无法重复创建。"
            )

        emby_config = await self.first_or_create_emby_config()
        if not emby_config:
            raise Exception("未找到 Emby 配置，无法创建账号。")

        if not await self._check_register_permission(user, emby_config):
            raise Exception("当前没有可用的注册权限或名额，创建账号被拒绝。")

        async with ConfigOrm().transaction() as session:
            if (
                not user.enable_register
                and emby_config.register_public_user > 0
            ):
                emby_config.register_public_user -= 1

            emby_config.total_register_user += 1
            new_user = await self._emby_create_user(
                telegram_id, username, password
            )

            session.add(new_user)
            session.add(emby_config)
            await session.commit()
        return new_user

    async def _check_register_permission(
        self, user: User, emby_config: Config
    ) -> bool:
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
            await ConfigOrm().update(
                values={"register_public_time": 0}, conds=[Config.id == 1]
            )
        return enable_register

    async def redeem_code(self, telegram_id: int, code: str):
        """使用邀请码，分为普通注册邀请码和白名单邀请码"""
        pattern = re.compile(r"^(epr|epw)-[A-Za-z0-9]+$")
        if not pattern.match(code):
            raise Exception("邀请码格式不正确。")

        user = await self.must_get_user(telegram_id)

        # 使用事务块，并通过行锁防止并发问题
        async with InviteCodeOrm().transaction() as session:
            # 构造 SELECT 语句，并加上 FOR UPDATE 行锁
            stmt = (
                select(InviteCode)
                .where(InviteCode.code == code)
                .with_for_update()
            )
            result = await session.execute(stmt)
            valid_code = result.scalars().first()

            if not valid_code or valid_code.is_used:
                raise Exception("该邀请码无效或已被使用。")

            # 根据邀请码类型执行不同的业务逻辑校验
            if valid_code.code_type == InviteCodeType.REGISTER:
                user.check_use_redeem_code()
            elif valid_code.code_type == InviteCodeType.WHITELIST:
                user.check_use_whitelist_code()
                if user.is_emby_baned():
                    await self.emby_unban(telegram_id)

            # 标记邀请码已使用，并记录使用时间和使用者
            valid_code.is_used = True
            valid_code.used_time = datetime.now().timestamp()
            valid_code.used_user_id = telegram_id

            # 根据邀请码类型更新用户状态
            if valid_code.code_type == InviteCodeType.REGISTER:
                user.enable_register = True
            elif valid_code.code_type == InviteCodeType.WHITELIST:
                user.is_whitelist = True

            session.add(valid_code)
            session.add(user)
            await session.commit()

        return valid_code

    async def reset_password(
        self, telegram_id: int, password: str = ""
    ) -> bool:
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
        self,
        telegram_id: int,
        reason: str,
        operator_telegram_id: Optional[int] = None,
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
            user.ban_time = int(datetime.now().timestamp())
            user.reason = reason
            await UserOrm().update(
                {"ban_time": user.ban_time, "reason": reason},
                conds=[User.id == user.id],
            )
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
            user.ban_time = 0
            user.reason = ""
            await UserOrm().update(
                {"ban_time": 0, "reason": None}, conds=[User.id == user.id]
            )
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

        if register_public_user is not None:
            emby_config.register_public_user = register_public_user
        if register_public_time is not None:
            emby_config.register_public_time = register_public_time

        await ConfigOrm().update(
            values={
                "register_public_user": emby_config.register_public_user,
                "register_public_time": emby_config.register_public_time,
            },
            conds=[Config.id == 1],
        )
        return emby_config

    def emby_count(self) -> Dict:
        """从 Emby API 获取当前影片数量统计"""
        return self.emby_api.count()

    async def get_user_router(self, telegram_id: int) -> Dict:
        """获取用户的线路信息"""
        user = await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.query_user_route(user.emby_id)

    async def update_user_router(
        self, telegram_id: int, new_index: str
    ) -> bool:
        """更新用户线路信息"""
        user = await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.update_user_route(
            str(user.emby_id), str(new_index)
        )

    async def get_router_list(self, telegram_id: int) -> List[Dict]:
        """获取所有可用线路"""
        await self.must_get_emby_user(telegram_id)
        return self.emby_router_api.query_all_route()
