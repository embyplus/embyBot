import logging
import aiohttp
import asyncio

logger = logging.getLogger(__name__)


class EmbyApi:
    """
    用于与 Emby 服务器交互的API封装，支持超时机制和异常处理。
    """

    def __init__(self, emby_url: str, emby_api: str, timeout: int = 10):
        """
        :param emby_url: Emby 服务器的基础 URL（例如：https://your-emby-server.com）
        :param emby_api: Emby 服务器的 API Key
        :param timeout: 每次请求的超时时间，默认为 10 秒
        """
        self.base_url: str = emby_url.rstrip("/")
        self.api_key: str = emby_api
        self.timeout: int = timeout
        logger.info(
            f"EmbyApi initialized with URL: {self.base_url}, timeout: {self.timeout}"
        )

    async def _request(self, method: str, path: str, data=None, params=None):
        """
        内部通用请求方法，用于简化 GET / POST 等请求的异常处理、状态码检查等。

        :param method: HTTP 方法，如 'GET' or 'POST'
        :param path: 接口路径（相对于 self.base_url 的相对路径）
        :param data: POST 请求体，通常为 JSON 格式
        :param params: URL 查询参数，将自动添加 api_key
        :return: 如果请求成功，返回响应的 JSON 内容；否则抛出异常
        """
        headers = {
            "X-MediaBrowser-Token": self.api_key,
            "Authorization": f"Token={self.api_key}",
            "X-Emby-Authorization": f"Token={self.api_key}",
            "User-Agent": "sadasd",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Content-Type": "application/json",
            "Accept": "*/*",
        }

        url = f"{self.base_url}{path}"
        logger.debug(
            f"Making {method} request to {url} with params: {params}, data: {data}"
        )
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            try:
                async with session.request(
                    method, url, params=params, json=data, headers=headers
                ) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Request failed with status code {response.status}"
                        )
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(
                    f"An error occurred while requesting Emby: {e}", exc_info=True
                )
                raise Exception(f"请求 Emby 时发生错误: {str(e)}")
            except asyncio.TimeoutError:
                logger.error("Request to Emby server timed out", exc_info=True)
                raise Exception("请求 Emby 服务器超时，请稍后重试或检查网络连接。")

    async def get_user(self, emby_id: str):
        """
        根据用户 ID 获取 Emby 用户信息。
        :param emby_id: Emby 用户 ID
        :return: 成功返回 JSON 数据，失败抛出异常
        """
        path = f"/emby/Users/{emby_id}"
        logger.info(f"Getting user with Emby ID: {emby_id}")
        try:
            return await self._request("GET", path)
        except Exception as e:
            logger.error(
                f"Failed to get user with Emby ID {emby_id}: {e}", exc_info=True
            )
            raise

    async def create_user(self, name: str):
        """
        在 Emby 中创建新用户。
        :param name: 用户名
        :return: 成功返回创建的用户信息 JSON，失败抛出异常
        """
        path = "/emby/Users/New"
        data = {"Name": name, "HasPassword": False}
        logger.info(f"Creating user with name: {name}")
        try:
            return await self._request("POST", path, data=data)
        except Exception as e:
            logger.error(f"Failed to create user with name {name}: {e}", exc_info=True)
            raise

    async def ban_user(self, emby_id: str):
        """
        禁用 Emby 用户：设置其 Policy，使其无法登录或观看。
        :param emby_id: Emby 用户 ID
        :return: 成功返回更新后的用户信息 JSON，失败抛出异常
        """
        data = {
            "IsAdministrator": False,
            "IsHidden": True,
            "IsHiddenRemotely": True,
            "IsDisabled": True,
            "EnableRemoteControlOfOtherUsers": False,
            "EnableSharedDeviceControl": False,
            "EnableRemoteAccess": False,
            "EnableLiveTvManagement": False,
            "EnableLiveTvAccess": False,
            "EnableMediaPlayback": True,
            "EnableAudioPlaybackTranscoding": False,
            "EnableVideoPlaybackTranscoding": False,
            "EnablePlaybackRemuxing": False,
            "EnableContentDeletion": False,
            "EnableContentDownloading": False,
            "EnableSubtitleDownloading": False,
            "EnableSubtitleManagement": False,
            "EnableSyncTranscoding": False,
            "EnableMediaConversion": False,
            "EnableAllDevices": True,
            "AllowCameraUpload": False,
            "SimultaneousStreamLimit": 0,
        }
        logger.info(f"Banning user with Emby ID: {emby_id}")
        try:
            return await self.update_user_policy(emby_id, data)
        except Exception as e:
            logger.error(
                f"Failed to ban user with Emby ID {emby_id}: {e}", exc_info=True
            )
            raise

    async def set_default_policy(self, emby_id: str):
        """
        取消禁用或为新建用户设置默认权限 Policy。
        :param emby_id: Emby 用户 ID
        :return: 成功返回更新后的用户信息 JSON，失败抛出异常
        """
        data = {
            "IsAdministrator": False,
            "IsHidden": True,
            "IsHiddenRemotely": True,
            "IsDisabled": False,
            "EnableRemoteControlOfOtherUsers": False,
            "EnableSharedDeviceControl": False,
            "EnableRemoteAccess": True,
            "EnableLiveTvManagement": False,
            "EnableLiveTvAccess": False,
            "EnableMediaPlayback": True,
            "EnableAudioPlaybackTranscoding": False,
            "EnableVideoPlaybackTranscoding": False,
            "EnablePlaybackRemuxing": False,
            "EnableContentDeletion": False,
            "EnableContentDownloading": False,
            "EnableSubtitleDownloading": False,
            "EnableSubtitleManagement": False,
            "EnableSyncTranscoding": False,
            "EnableMediaConversion": False,
            "EnableAllDevices": True,
            "AllowCameraUpload": False,
            "SimultaneousStreamLimit": 3,
        }
        logger.info(f"Setting default policy for user with Emby ID: {emby_id}")
        try:
            return await self.update_user_policy(emby_id, data)
        except Exception as e:
            logger.error(
                f"Failed to set default policy for user with Emby ID {emby_id}: {e}",
                exc_info=True,
            )
            raise

    async def update_user_policy(self, emby_id: str, policy_data: dict):
        """
        更新 Emby 用户的 policy 设置，如是否禁用、并发数等。
        :param emby_id: Emby 用户 ID
        :param policy_data: 要更新的 policy 字段
        :return: 成功返回更新后的用户信息 JSON，失败抛出异常
        """
        path = f"/emby/Users/{emby_id}/Policy"
        logger.info(
            f"Updating user policy for Emby ID: {emby_id} with data: {policy_data}"
        )
        try:
            return await self._request("POST", path, data=policy_data)
        except Exception as e:
            logger.error(
                f"Failed to update user policy for Emby ID {emby_id}: {e}",
                exc_info=True,
            )
            raise

    async def reset_user_password(self, emby_id: str):
        """
        重置用户密码（让 Emby 忘记当前密码，此后需要重新设置新密码）。
        :param emby_id: Emby 用户 ID
        :return: 成功返回结果 JSON，失败抛出异常
        """
        path = f"/emby/users/{emby_id}/Password"
        data = {"ResetPassword": True}
        logger.info(f"Resetting password for user with Emby ID: {emby_id}")
        try:
            return await self._request("POST", path, data=data)
        except Exception as e:
            logger.error(
                f"Failed to reset password for user with Emby ID {emby_id}: {e}",
                exc_info=True,
            )
            raise

    async def set_user_password(self, emby_id: str, new_pass: str):
        """
        设置指定 Emby 用户的新密码。
        :param emby_id: Emby 用户 ID
        :param new_pass: 新密码
        :return: 成功返回结果 JSON，失败抛出异常
        """
        path = f"/emby/users/{emby_id}/Password"
        data = {"ResetPassword": False, "CurrentPw": "", "NewPw": new_pass}
        logger.info(f"Setting password for user with Emby ID: {emby_id}")
        try:
            return await self._request("POST", path, data=data)
        except Exception as e:
            logger.error(
                f"Failed to set password for user with Emby ID {emby_id}: {e}",
                exc_info=True,
            )
            raise

    async def check_emby_site(self) -> bool:
        """
        检查 Emby 是否可用，仅做简单的 200 检查。
        :return: 若状态码为 200 则返回 True，否则抛出异常或返回 False
        """
        path = "/emby/System/Info"
        logger.info("Checking Emby site availability")
        try:
            await self._request("GET", path)
            return True
        except Exception as e:
            logger.warning(f"Emby site check failed: {e}", exc_info=True)
            return False

    async def count(self):
        """
        获取 Emby 中影视的数量汇总。
        :return: 包含影视数量信息的 JSON
        """
        path = "/emby/Items/Counts"
        logger.info("Getting Emby item counts")
        try:
            return await self._request("GET", path)
        except Exception as e:
            logger.error(f"Failed to get Emby item counts: {e}", exc_info=True)
            raise


class EmbyRouterAPI:
    """
    如果有多条线路可供用户选择，封装了对 Emby Router 服务器的 API 访问。
    """

    def __init__(self, api_url: str, api_key: str = "", timeout: int = 10):
        """
        :param api_url: 路由服务的基础URL
        :param api_key: 路由服务使用的Token（如果需要鉴权）
        :param timeout: 请求超时，默认为10秒
        """
        self.api_url = api_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        logger.info(
            f"EmbyRouterAPI initialized with URL: {self.api_url}, timeout: {self.timeout}"
        )

    async def call_api(self, path: str):
        """
        路由API通用请求方法。
        :param path: API路径
        :return: 成功时返回 JSON，失败抛出异常
        """
        url = f"{self.api_url}{path}"
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        logger.debug(f"Calling API at {url}")
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        ) as session:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise Exception(
                            f"Request failed with status code {response.status}"
                        )
                    return await response.json()
            except aiohttp.ClientError as e:
                logger.error(
                    f"An error occurred while requesting router service: {e}",
                    exc_info=True,
                )
                raise Exception(f"请求路由服务时发生错误: {str(e)}")
            except asyncio.TimeoutError:
                logger.error("Request to router service timed out", exc_info=True)
                raise Exception("请求路由服务超时，请稍后重试或检查网络连接。")

    async def query_all_route(self):
        """
        获取所有可用线路。
        """
        logger.info("Querying all routes")
        try:
            return await self.call_api("/api/route")
        except Exception as e:
            logger.error(f"Failed to query all routes: {e}", exc_info=True)
            raise

    async def query_user_route(self, user_id: str):
        """
        获取指定用户当前所选的线路信息。
        """
        logger.info(f"Querying user route for user ID: {user_id}")
        try:
            return await self.call_api(f"/api/route/{user_id}")
        except Exception as e:
            logger.error(
                f"Failed to query user route for user ID {user_id}: {e}", exc_info=True
            )
            raise

    async def update_user_route(self, user_id: str, new_index: str):
        """
        更新用户当前所使用的线路。
        """
        logger.info(f"Updating user route for user ID: {user_id} to index: {new_index}")
        try:
            return await self.call_api(f"/api/route/{user_id}/{new_index}")
        except Exception as e:
            logger.error(
                f"Failed to update user route for user ID {user_id} to index {new_index}: {e}",
                exc_info=True,
            )
            raise
