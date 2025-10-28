from typing import Any
from locust import HttpUser, task, between

from enums.loglabelEnum import LogLabelEnum
from enums.nosqlEnum import NosqlEnum
from utils.logs import ExceptionLog
from utils.nosql_pool import TokenPool
from utils.file_control import get_diff_env_url

class BrowseOnly(HttpUser):
    host: str | None = get_diff_env_url()
    wait_time = between(0, 5) # constant(2)为固定时间执行动作

    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance(),
        token_pool: TokenPool = TokenPool.get_instance()
    ) -> None:
        super().__init__()
        self._e: ExceptionLog = e
        self._headers: dict = {}
        self._token_pool: TokenPool = token_pool

    def on_start(self) -> None:
        auth_token: str | None = self._token_pool.get_access_token()
        if auth_token is None:
            self._e.error("%s 可用token为空,终止测试", LogLabelEnum.ERROR.value)
            self.stop()
        assert auth_token is not None
        self._headers.setdefault(NosqlEnum.AUTHORIZATION.value, auth_token)
        self.client.headers.update(self._headers)

    @task(5)
    def view_home_page(self) -> None:
        try:
            with self.client.get(
                "/",
                headers=self._headers,
                catch_response=True,
                name="%s 浏览首页" % LogLabelEnum.TEST.value
            ) as resp:
                if resp.status_code != 200:
                    fail_mess: str = f"{LogLabelEnum.ERROR.value} 浏览首页失败,失败原因: {resp.text}" 
                    self._e.error(fail_mess)
                    resp.failure(fail_mess)
                else:
                    self._e.info("%s 浏览首页成功", LogLabelEnum.SUCCESS.value)
                    resp.success()
        except Exception as err:
            self._e.handle_exception(err)
            self._e.error("%s 浏览首页异常,异常原因: %s", LogLabelEnum.ERROR.value, err)
            self.stop()
