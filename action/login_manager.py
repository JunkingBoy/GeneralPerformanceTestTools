import requests
import threading

from pathlib import Path
from typing import Optional

from template.nosqlTemplate import UserData
from template.httpTemplate import StandardReqDataTemplate

from enums.nosqlEnum import NosqlEnum
from enums.serverEnum import ServerEnum
from enums.actionEnum import ActionEnum
from enums.loglabelEnum import LogLabelEnum
from enums.csvEnum import CsvReadEnmum
from utils.logs import ExceptionLog
from utils.csv_div import CsvOperator
from utils.nosql import NosqlOperator
from utils.file import get_env_val
from utils.request import RequestAction
from check.standar import standard_normal_check

class LoginAction:
    '''
    TODO:
    1.重新设计登录逻辑.可以封装成一个方法 - 登录逻辑的问题是耦合太严重
    2.这个类本身应该是一个组装工厂,依赖下层提供的方法进行数据组装实现读取数据、登录、数据写入的功能
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

    def action_login(self) -> None:
        # 通过csv获取用户数据
        csv_p: Path = Path(__file__).parent.parent / "csv_data"
        if not csv_p.exists():
            self._e.error("%s csv文件目录不存在", LogLabelEnum.ERROR.value)
            return
        csv_f_p: Path = csv_p / "csv_user_data.csv"
        if not csv_f_p.exists() or not csv_f_p.is_file():
            self._e.error("%s csv文件不存在", LogLabelEnum.ERROR.value)
            return
        if not str(csv_f_p).endswith(".csv"):
            self._e.error("%s csv文件格式错误", LogLabelEnum.WARNING.value)
            return
        u_d: list = self._csv.get_csv_data(str(csv_f_p))
        if not u_d:
            self._e.error("%s csv文件数据为空", LogLabelEnum.INFO.value)
            return
        # 调用requests进行登录
        host: str | None = get_env_val()
        uri: str = f"{host}{ActionEnum.LOGIN_TEST.value}"
        for u in u_d:
            if not u.get(CsvReadEnmum.PHONE.value) and not u.get(CsvReadEnmum.PASSWORD.value): break
            login_body: dict = {
                CsvReadEnmum.PHONE.value: u.get(CsvReadEnmum.PHONE.value),
                CsvReadEnmum.PASSWORD.value: u.get(CsvReadEnmum.PASSWORD.value)
            }
            req_data: StandardReqDataTemplate = StandardReqDataTemplate(
                url=uri,
                method="POST",
                params=None,
                headers={"sec-ch-ua-platform": "apitest"},
                form=None,
                body=login_body
            )
            req: RequestAction = RequestAction(self._e)
            resp: tuple | None = req.request_meta(req_data)
            if resp is None: continue
            res_data: UserData | None = standard_normal_check(resp[0], resp[1], resp[2])
            if res_data is None: continue
            else:
                self._e.info("%s 登录成功,用户名: %s", LogLabelEnum.SUCCESS.value, u.get(CsvReadEnmum.PHONE.value))
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
        host: str | None = get_env_val()
        uri: str = f"{host}{ActionEnum.LOGIN_TEST.value}"
        username: str = list(ret_data.keys())[0]
        password: str = ret_data.get(username).get(NosqlEnum.PASSWORD.value) # type: ignore
        login_body: dict = {
            CsvReadEnmum.PHONE.value: username,
            CsvReadEnmum.PASSWORD.value: password
        }
        req_data: StandardReqDataTemplate = StandardReqDataTemplate(
            url=uri,
            method="POST",
            params=None,
            headers={"sec-ch-ua-platform": "apitest"},
            form=None,
            body=login_body
        )
        req: RequestAction = RequestAction(self._e)
        resp: tuple | None = req.request_meta(req_data)
        if resp is None:
            self._e.error("%s 重登失败,请检查网络", LogLabelEnum.ERROR.value)
            return
        res_data: UserData | None = standard_normal_check(resp[0], resp[1], resp[2])
        if res_data is None:
            self._e.error("%s 重登请求成功,业务响应校验失败", LogLabelEnum.ERROR.value)
            return
        else:
            self._e.info("%s 重登成功,用户名: %s", LogLabelEnum.RETRY.value, username)
            self._nosql.update(username, res_data.metadata)
