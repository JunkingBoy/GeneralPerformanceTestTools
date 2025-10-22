import io
import os
import csv
import threading

from typing import Optional
from pathlib import Path

from utils.encry import UnitEncry
from utils.logs import ExceptionLog

class CsvCore:
    '''
    该类的职责:
    1.负责csv文件的签名发放
    2.负责csv文件的签名验证
    '''
    __instance: Optional['CsvCore'] = None
    __lock: threading.Lock = threading.Lock()

    @staticmethod
    def get_instance() -> 'CsvCore':
        if CsvCore.__instance: return CsvCore.__instance
        else:
            with CsvCore.__lock:
                if not CsvCore.__instance: CsvCore.__instance = CsvCore()
            return CsvCore.__instance

    def __init__(
        self,
        encry: UnitEncry = UnitEncry()
    ) -> None:
        if hasattr(self, "__initialized") and self.__initialized:
            return
        else:
            self._e: ExceptionLog = ExceptionLog.get_instance()
            self._key_manager: UnitEncry = encry
            self.__initialized: bool = True

    def _set_csv_meta_data(self) -> None:
        target_dir: Path = Path(__file__).parent.parent / "csv_template"
        if not target_dir.exists():
            target_dir.mkdir(parents=True, exist_ok=True)
            self._e.info("初始化csv模板文件夹成功")
        csv_template_file: Path = target_dir / "csv_template.csv"
        if not csv_template_file.exists():
            csv_template_file.touch()
            self._e.info("初始化csv模板文件成功")
        self._csv_template: str = str(csv_template_file)
        ...

