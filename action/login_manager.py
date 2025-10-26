import threading

from typing import Optional

from utils.logs import ExceptionLog
from utils.csv_div import CsvOperator
from utils.nosql import NosqlOperator

class LoginAction:
    '''
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

    def __init_(
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
