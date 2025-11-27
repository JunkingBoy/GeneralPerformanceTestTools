import os
import copy
import threading
import pandas as pd

from typing import Optional
from utils.logs import ExceptionLog

class InsertManager:
    '''
    该类的职责是
    1.专门处理数据插入逻辑
    2.处理数据读取逻辑
    '''
    __instance: Optional['InsertManager'] = None
    __lock: threading.Lock = threading.Lock()

    @staticmethod
    async def get_instance() -> 'InsertManager':
        if InsertManager.__instance: return InsertManager.__instance
        else:
            with InsertManager.__lock:
                if not InsertManager.__instance: InsertManager.__instance = InsertManager()
            return InsertManager.__instance

    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance()
    ) -> None:
        if hasattr(self, "_initialized") and self._initialized:
            return
        else:
            self._test_result_bf: pd.DataFrame = pd.DataFrame()
            self._e: ExceptionLog = e
            self._initialized: bool = True

    @property
    def is_test_result_bf_empty(self) -> bool:
        return self._test_result_bf.empty

    def _clear_test_result_bf(self) -> None:
        self._test_result_bf = pd.DataFrame()

    def add_test_result_bf(self, result: dict) -> None:
        if not isinstance(result, dict):
            self._e.error("参数类型错误: %s", type(result))
            return
        temp_dict: dict = copy.deepcopy(result)
        with InsertManager.__lock:
            new_entry: pd.DataFrame = pd.DataFrame(
                [temp_dict]
            )
            self._test_result_bf = pd.concat(
                [self._test_result_bf, new_entry],
                ignore_index=True
            )
            self._e.info("添加测试结果: %s", temp_dict)

    def del_test_result(self) -> None:
        self._clear_test_result_bf()

    def save_test_result(self, file_path: str) -> None:
        if not os.path.exists(file_path):
            self._e.error("目标文件不存在: %s", file_path)
            return

        _, ext = os.path.splitext(file_path)
        supported_exts: list = [".xlsx", ".xls", ".csv"]

        if ext.lower() not in supported_exts:
            self._e.error("不支持的文件格式: %s", ext)
            return
        match ext.lower():
            case ".csv":
                self._test_result_bf.to_csv(
                    str(file_path),
                    index=False,
                    encoding="utf-8-sig",
                    mode="w"
                )
                self._e.info("数据已保存为CSV文件: %s", file_path)
            case _:
                self._test_result_bf.to_excel(
                    str(file_path),
                    index=False,
                    engine="openpyxl"
                )
                self._e.info("数据已保存为Excel文件: %s", file_path)
        self._clear_test_result_bf()
