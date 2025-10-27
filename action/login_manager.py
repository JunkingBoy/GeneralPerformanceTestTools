import os
import requests
import threading

from pathlib import Path
from typing import Optional

from template.nosqlTemplate import UserData, MetaUserData
from template.httpTemplate import HttpReqTemplate

from enums.nosqlEnum import NosqlEnum
from enums.serverEnum import ServerEnum
from enums.actionEnum import ActionEnum
from enums.loglabelEnum import LogLabelEnum
from utils.logs import ExceptionLog
from utils.csv_div import CsvOperator
from utils.nosql import NosqlOperator
from utils.file_control import get_diff_env_url

class LoginAction:
    '''
    TODO:
    1.重新设计登录逻辑.可以封装成一个方法
    管理用户登录
    1.从csv读取用户信息
    2.通过定义的模板类进行用户登录
    3.登录数据写入nosql
    '''
    __instance: Optional['LoginAction'] = None
    __lock: threading.Lock = threading.Lock()

    @staticmethod
    def get_instance() -> 'LoginAction':
        if LoginAction.__instance: return LoginAction.__instance
        else:
            with LoginAction.__lock:
                if not LoginAction.__instance: LoginAction.__instance = LoginAction()
            return LoginAction.__instance

    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance(),
        csv: CsvOperator = CsvOperator.create(),
        nosql: NosqlOperator = NosqlOperator.create()
    ) -> None:
        if hasattr(self, "__initialized") and self.__initialized:
            return
        else:
            self._e: ExceptionLog = e
            self._csv: CsvOperator = csv
            self._nosql: NosqlOperator = nosql
            self.__initialized: bool = True

    def _login(self, req_kwargs: dict) -> UserData | None:
        if not req_kwargs:
            self._e.error("%s 请求参数错误", LogLabelEnum.ERROR.value)
            return
        with requests.request(**req_kwargs) as r:
            if r.status_code != 200:
                self._e.error("%s 请求失败", LogLabelEnum.ERROR.value)
                return
            else:
                try:
                    resp: dict = r.json()
                    res_code: int = resp.get("code", 0)
                    if res_code != ServerEnum.SUCCESS.value:
                        self._e.error("%s 登录失败,服务端状态码: %s", LogLabelEnum.ERROR.value, res_code)
                        return
                    self._e.info("%s 用户登录成功", LogLabelEnum.SUCCESS.value)
                    auth: str = resp.get("data", {}).get("token")
                    username: str = req_kwargs.get("json", {}).get("phone")
                    password: str = req_kwargs.get("json", {}).get("password")
                    if not auth:
                        self._e.error("%s 用户登录成功,获取token失败", LogLabelEnum.INFO.value)
                        return
                    ins_data: UserData = UserData(
                        username=username,
                        metadata=MetaUserData(
                            password=password,
                            Authorization=auth
                        )
                    )
                    return ins_data
                except Exception as err:
                    self._e.handle_exception(err)
                    self._e.error("%s 登录失败,失败原因: %s", LogLabelEnum.ERROR.value, err)
                    return

    def action_login(self) -> None:
        # 通过csv获取用户数据
        csv_p: Path = Path(__file__).parent.parent / "csv_data"
        if not csv_p.exists():
            self._e.error("%s csv文件目录不存在", LogLabelEnum.ERROR.value)
            return
        csv_f_p: Path = csv_p / "csv_user_data.csv"
        if not csv_f_p.exists() or not os.path.isfile(csv_f_p):
            self._e.error("%s csv文件不存在", LogLabelEnum.ERROR.value)
            return
        if not str(csv_f_p).endswith(".csv"):
            self._e.error("%s csv文件格式错误", LogLabelEnum.INFO.value)
            return
        u_d: list = self._csv.get_csv_data(str(csv_f_p))
        if not u_d:
            self._e.error("%s csv文件数据为空", LogLabelEnum.INFO.value)
            return
        # 调用requests进行登录
        host: str = get_diff_env_url()
        uri: str = f"{host}{ActionEnum.LOGIN_TEST.value}"
        req_kwargs: dict = HttpReqTemplate(
            url=uri,
            method="POST",
            params=None,
            headers={"sec-ch-ua-platform": "apitest"}
        ).info
        for u in u_d:
            if not u[0] and not u[1]: break
            login_body: dict = {
                "phone": u[0],
                "password": u[1]
            }
            req_kwargs.update({"json": login_body})
            res_data: UserData | None = self._login(req_kwargs)
            if res_data is None: continue
            else:
                self._e.info("%s 登录成功,用户名: %s", LogLabelEnum.SUCCESS.value, u[0])
                self._nosql.insert(res_data)

    def retry(self, auth: str) -> None:
        if not auth:
            self._e.error("%s token为空", LogLabelEnum.INFO.value)
            return
        ret_data: dict | None = self._nosql.get_data_by_auth(auth)
        if ret_data is None:
            self._e.error("%s token不在数据库中", LogLabelEnum.INFO.value)
            return
        # 调用requests进行登录
        host: str = get_diff_env_url()
        uri: str = f"{host}{ActionEnum.LOGIN_TEST.value}"
        req_kwargs: dict = HttpReqTemplate(
            url=uri,
            method="POST",
            params=None,
            headers={"sec-ch-ua-platform": "apitest"}
        ).info
        username: str = list(ret_data.keys())[0]
        password: str = ret_data.get(username).get(NosqlEnum.PASSWORD.value) # type: ignore
        login_body: dict = {
            "phone": username,
            "password": password
        }
        req_kwargs.update({"json": login_body})
        res_data: UserData | None = self._login(req_kwargs)
        if res_data is None: return
        else:
            self._e.info("%s 重登成功,用户名: %s", LogLabelEnum.RETRY.value, username)
            self._nosql.update(username, res_data.metadata)
