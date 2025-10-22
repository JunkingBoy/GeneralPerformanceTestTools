import os
import logging
import threading

from typing import Optional
from datetime import datetime
from rich.logging import RichHandler

from enums.errEnum import eEnum
from template.logTemplate import LogData

class ExceptionLog:
    __instance: Optional['ExceptionLog'] = None
    __lock: threading.Lock = threading.Lock()

    @staticmethod
    def get_instance() -> 'ExceptionLog':
        if ExceptionLog.__instance: return ExceptionLog.__instance
        else:
            with ExceptionLog.__lock:
                if not ExceptionLog.__instance: ExceptionLog.__instance = ExceptionLog()
            return ExceptionLog.__instance

    def __init__(
        self
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        else:
            '''
            初始化日志记录器以及处理器
            '''
            self._err_log: str = "logs/err"
            self._info_log: str = "logs/info"

            self.logger: logging.Logger = logging.getLogger("ExceptionLog")
            if self.logger.handlers:
                self._initialized: bool = True
                return

            self.logger.setLevel(logging.DEBUG)

            os.makedirs(self._err_log, exist_ok=True)
            os.makedirs(self._info_log, exist_ok=True)

            # 添加 RichHandler - 用于终端美化输出
            rich_handler: RichHandler = RichHandler(
                show_time=True,
                show_path=False,
                markup=True,
                rich_tracebacks=True, # 使用 rich 格式化异常追踪
                tracebacks_show_locals=True # 在异常追踪中显示局部变量
            )
            rich_handler.setLevel(logging.INFO)
            self.logger.addHandler(rich_handler)

            # 创建处理器a
            self._err_file_name: str = f"{self._err_log}/{datetime.now().strftime('%Y-%m-%d')}.log"
            err_handler: logging.FileHandler = logging.FileHandler(
                self._err_file_name,
                encoding='utf-8-sig',
                mode='a' # 追加写入,文件存在则在文件末尾添加内容
            )

            err_handler.setLevel(logging.ERROR)
            err_handler_fmt: logging.Formatter = logging.Formatter(
                "%(asctime)s:%(pathname)s:%(name)s:%(levelname)s:%(message)s"
            )
            err_handler.setFormatter(err_handler_fmt)
            # 为记录器添加处理器
            self.logger.addHandler(err_handler)

            # 创建处理器b
            self._info_file_name: str = f"{self._info_log}/run.log"
            info_handler: logging.FileHandler = logging.FileHandler(
                self._info_file_name,
                encoding="utf-8-sig",
                mode='w' # 重写模式
            )
            info_handler.setLevel(logging.INFO)
            info_handler_fmt: logging.Formatter = logging.Formatter(
                "%(asctime)s:%(levelname)s:%(message)s"
            )
            info_handler.setFormatter(info_handler_fmt)
            self.logger.addHandler(info_handler)

            self._initialized: bool = True

    @property
    def err_file_dir(self) -> str:
        return self._err_log

    @property
    def err_file_path(self) -> str:
        return self._err_file_name

    @property
    def info_file_dir(self) -> str:
        return self._info_log

    @property
    def info_file_path(self) -> str:
        return self._info_file_name

    def handle_exception(self, e: Exception) -> None:
        # 由于IOerror和ConnectionError是OSError的子类，所以这里不用match-case进行匹配
        if isinstance(e, TypeError):
            err_data: LogData = LogData(eEnum.TYPEFAIL, "")
            self.logger.error(
                f"类型错误: {err_data.message}",
                extra={"code": err_data.code},
                exc_info=True
            )
        elif isinstance(e, AttributeError):
            err_data: LogData = LogData(eEnum.ATTRIBUTEFAIL, "")
            self.logger.error(
                f"属性错误: {err_data.message}",
                extra={"code": err_data.code},
                exc_info=True
            )
        elif isinstance(e, ConnectionError):
            err_data: LogData = LogData(eEnum.CONNECTFAIL, "")
            self.logger.error(
                f"链接错误: {err_data.message}",
                extra={"code": err_data.code},
                exc_info=True
            )
        elif isinstance(e, OSError):
            err_data: LogData = LogData(eEnum.OSFAIL, "")
            self.logger.error(
                f"OS错误: {err_data.message}",
                extra={"code": err_data.code},
                exc_info=True
            )
        else:
            err_data: LogData = LogData(eEnum.UNKNOWNFAIL, "")
            self.logger.error(
                f"未知错误: {err_data.message}",
                extra={"code": err_data.code},
                exc_info=True
            )

    def info(self, logmsgformat: str, *args) -> None:
        self.logger.info(logmsgformat, *args)

    def error(self, logmsgformat: str, *args) -> None:
        self.logger.error(logmsgformat, *args)
