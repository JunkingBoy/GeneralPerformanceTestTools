import io
import os
import csv
import threading

from pathlib import Path
from typing import Optional

from utils.encry import UnitEncry
from utils.logs import ExceptionLog
from enums.csvEnum import CsvMetaEnum, CsvHeaderEnum
from enums.loglabelEnum import LogLabelEnum

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
            self._e.info("%s 初始化csv模板文件夹成功", LogLabelEnum.SUCCESS.value)
        csv_template_file: Path = target_dir / "csv_template.csv"
        if not csv_template_file.exists():
            csv_template_file.touch()
            self._e.info("%s 初始化csv模板文件成功", LogLabelEnum.SUCCESS.value)
        self._csv_template: str = str(csv_template_file)
        if not hasattr(self._key_manager, "_rsa_pub_key") or not hasattr(self._key_manager, "_key"):
            self._e.error("%s 初始化加密密钥失败", LogLabelEnum.ERROR.value)
            return
        # 加密表头
        csv_header: str = CsvHeaderEnum.get_headers_str()
        csv_header_list: list = CsvHeaderEnum.get_headers_list()
        sig_str: str = self._key_manager.generate_encry_str(csv_header)
        # 加密公钥
        encry_pub: str = self._key_manager.generate_encry_str(self._key_manager.rsa_pub_key)
        # 元数据写入csv
        try:
            with open(self._csv_template, "w", encoding="utf-8", newline="") as f:
                csv_w = csv.writer(f)
                csv_w.writerow([CsvMetaEnum.SIG.value, sig_str])
                csv_w.writerow([CsvMetaEnum.PUB_ENCRY_KEY.value, encry_pub])
                csv_w.writerow(csv_header_list)
            self._e.info("%s 初始化csv元数据成功,csv模板已生成: %s", LogLabelEnum.SUCCESS.value, self._csv_template)
            return
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("%s 写入csv元数据失败", LogLabelEnum.ERROR.value)
            return

