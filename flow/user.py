from locust import HttpUser, task, between

from enums.loglabelEnum import LogLabelEnum
from enums.nosqlEnum import NosqlEnum
from utils.logs import ExceptionLog
from utils.manager import TokenPool
from utils.file import get_env_val
from enums.serverEnum import ServerEnum

class BrowseOnly(HttpUser):
    # 多实例共享同一个用户池
    __user_pool: list = []
    host: str | None = get_env_val()
    wait_time = between(0, 5) # constant(2)为固定时间执行动作

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._e: ExceptionLog = ExceptionLog.get_instance()
        self._headers: dict = {}
        self._token_pool: TokenPool = TokenPool.get_instance()

    def on_start(self) -> None:
        result: tuple | None = self._token_pool.get_access_token()
        if result is None:
            self._e.error("%s 可用token为空,提供测试数据不足", LogLabelEnum.ERROR.value)
            self.stop()
            return
        user, auth_token = result
        self.__user_pool.append(user)
        self._headers.setdefault(NosqlEnum.AUTHORIZATION.value, auth_token)
        self._headers.setdefault("sec-ch-ua-platform", "apitest")
        self.client.headers.update(self._headers)
        self._e.info("%s 获取用户token成功,用户ID: %s 绑定账号: %s", LogLabelEnum.GREENLIGHT.value, id(self), user)

    def on_stop(self):
        if self.__user_pool:
            for user in self.__user_pool:
                self._token_pool.cast_token(user)
                self._e.info("%s 释放用户token成功,用户ID: %s 释放账号: %s", LogLabelEnum.RETRY.value, id(self), user)

    @task(5)
    def view_home_page(self) -> None:
        try:
            with self.client.get(
                "/user/info",
                headers=self._headers,
                catch_response=True,
                name="%s 测试获取用户信息" % LogLabelEnum.TEST.value
            ) as resp:
                if resp.status_code != 200 or not resp.json().get("code") != ServerEnum.SUCCESS.value:
                    fail_mess: str = f"{LogLabelEnum.ERROR.value} 获取用户信息失败,失败原因: {resp.text}" 
                    self._e.error(fail_mess)
                    resp.failure(fail_mess)
                else:
                    self._e.info("%s 获取用户信息成功,用户信息: %s", LogLabelEnum.SUCCESS.value, resp.text)
                    resp.success()
        except Exception as err:
            self._e.handle_exception(err)
            self._e.error("%s 获取用户信息异常,异常原因: %s", LogLabelEnum.ERROR.value, err)
            self.stop()
