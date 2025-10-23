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
    TODO:
    1.完善解析文件方法
    2.思考是否有必要对csv进行签发、验证
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
        csv_header_list: list = CsvHeaderEnum.get_headers_list()
        encry_sig: str = self._key_manager.generate_signature_str(csv_header_list)
        # 加密公钥
        encry_pub: str = self._key_manager.generate_encry_str(self._key_manager.rsa_pub_key)
        # 元数据写入csv
        try:
            with open(self._csv_template, "w", encoding="utf-8", newline="") as f:
                csv_w = csv.writer(f)
                csv_w.writerow([f"#{CsvMetaEnum.SIG.value}:{encry_sig}"])
                csv_w.writerow([f"#{CsvMetaEnum.PUB_ENCRY_KEY.value}:{encry_pub}"])
                csv_w.writerow(csv_header_list)
            self._e.info("%s 初始化csv元数据成功,csv模板已生成: %s", LogLabelEnum.SUCCESS.value, self._csv_template)
            return
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("%s 写入csv元数据失败", LogLabelEnum.ERROR.value)
            return

    def _is_source_csv(self, csv_file: str) -> bool:
        if not csv_file: return False
        if not os.path.exists(csv_file):
            self._e.error("%s csv文件不存在", LogLabelEnum.ERROR.value)
            return False
        try:
            csv_bytes: bytes = Path(csv_file).read_bytes()
            lines: list = csv_bytes.decode("utf-8").splitlines()
            if len(lines) < 3:
                self._e.error("%s csv文件格式错误", LogLabelEnum.UNSPORTED.value)
                return False
            reader = csv.reader(lines)
            meta_sig: str = ""
            meta_pub: str = ""
            meta_header: list = []
            # 只取前三行数据进行数据校验
            for row in reader:
                if row[0].startswith(f"#{CsvMetaEnum.SIG.value}"): meta_sig = row[0].split(":")[1].strip()
                elif row[0].startswith(f"#{CsvMetaEnum.PUB_ENCRY_KEY.value}"): meta_pub = row[0].split(":")[1].strip()
                elif row[0].startswith("#"): continue
                else: meta_header = row
            if not meta_sig or not meta_pub or not meta_header:
                self._e.error("%s csv文件错误", LogLabelEnum.UNSPORTED.value)
                return False
            # 验证公钥是否相同
            if self._key_manager.parse_encry_str(meta_pub) != self._key_manager.rsa_pub_key:
                self._e.error("%s csv文件公钥错误", LogLabelEnum.ERROR.value)
                return False
            # 验证签名
            if not self._key_manager.verify_signature(meta_header, meta_sig):
                self._e.error("%s csv文件签名错误", LogLabelEnum.ERROR.value)
                return False
            self._e.info("%s csv文件验证成功", LogLabelEnum.SIGNATURE.value)
            return True
        except Exception as err:
            self._e.handle_exception(err)
            self._e.error("%s 验证csv文件失败", LogLabelEnum.ERROR.value)
            return False
