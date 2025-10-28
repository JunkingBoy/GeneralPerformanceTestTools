import json
import copy
import threading

from pathlib import Path
from datetime import datetime
from typing import Optional

from utils.logs import ExceptionLog
from enums.nosqlEnum import NosqlEnum
from template.nosqlTemplate import UserData, MetaUserData

class NosqlCore:
    __instance: Optional['NosqlCore'] = None
    __lock: threading.Lock = threading.Lock()

    @staticmethod
    def get_instance() -> 'NosqlCore':
        if NosqlCore.__instance: return NosqlCore.__instance
        else:
            with NosqlCore.__lock:
                if not NosqlCore.__instance: NosqlCore.__instance = NosqlCore()
            return NosqlCore.__instance

    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance(),
    ) -> None:
        if hasattr(self, "__initialized") and self.__initialized:
            return
        else:
            self._e: ExceptionLog = e
            self._data_folder: str = "nosql"
            self._data_file: str = "user_data.json"
            self._init_nosql()
            self.__initialized: bool = True

    def _init_nosql(self) -> None:
        target_path: Path = Path(__file__).parent.parent / self._data_folder
        if not target_path.exists(): target_path.mkdir()
        nosql_file: Path = target_path / self._data_file
        if not nosql_file.exists():
            nosql_file.touch()
            with open(str(nosql_file), "w", encoding="utf-8") as f: f.write("{}")
            self._e.info("缓存数据库初始化完成")
        else:
            self._e.info("缓存数据库已存在")
        self._nosql_file: str = str(nosql_file)

    def _write_nosql_data(self, data: dict) -> bool:
        try:
            with self.__lock:
                with open(self._nosql_file, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
            self._e.info("缓存数据库写入数据成功")
            return True
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库写入数据失败,失败原因: %s", e)
            return False

    def _get_nosql_data(self) -> dict | None:
        if not hasattr(self, "_nosql_data"): self._init_nosql()
        try:
            with open(self._nosql_file, "r", encoding="utf-8") as f: n_data: dict = json.load(f)
            return copy.deepcopy(n_data) # 返回深拷贝
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库获取数据失败,失败原因: %s", e)
            return

    def _get_nosql_data_by_auth(self, key: str) -> dict | None:
        if not hasattr(self, "_nosql_data"): self._init_nosql()
        try:
            with open(self._nosql_file, "r", encoding="utf-8") as f: n_data: dict = json.load(f)
            if not n_data: return
            res: dict = {}
            for k, v in n_data.items():
                if v.get("Authorization") != key: continue
                else: res.setdefault(k, v)
            return copy.deepcopy(res)
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库获取数据失败,失败原因: %s", e)
            return

    def _insert_nosql_data(self, data: UserData) -> bool:
        # 直接插入缓存数据库.如果数据存在那么直接覆盖.login_time直接更新
        if not isinstance(data, UserData):
            self._e.error("数据库插入数据类型错误, 需要类型: %s, 实际类型: %s", type(UserData), type(data))
            return False
        try:
            nosql_data: dict | None = self._get_nosql_data()
            if nosql_data is None: return False
            tmp_meta_data: dict = data.metadata.info
            tmp_meta_data.update({NosqlEnum.LOGIN_TIME.value: str(datetime.now().isoformat())})
            tmp_meta_data.update({NosqlEnum.UPDATE_TIME.value: str(datetime.now().isoformat())})
            nosql_data.update({str(data.key): tmp_meta_data})
            self._e.info("缓存数据库插入数据成功,时间: %s", str(datetime.now().isoformat()))
            return self._write_nosql_data(nosql_data)
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库插入数据失败,失败原因: %s, 时间: %s", e, str(datetime.now().isoformat()))
            return False

    def _delete_nosql_data(self, key: str) -> bool:
        try:
            nosql_data: dict | None = self._get_nosql_data()
            if nosql_data is None: return False
            nosql_data.pop(key, None)
            return self._write_nosql_data(nosql_data)
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库删除数据失败,失败原因: %s", e)
            return False

    def _update_nosql_data(self, key: str, data: MetaUserData) -> bool:
        try:
            if not key:
                self._e.error("键值不能为空")
                return False
            nosql_data: dict | None = self._get_nosql_data()
            if nosql_data is None:
                self._e.error("缓存数据库无数据")
                return False
            if nosql_data.get(str(key)) is None:
                self._e.info("用户数据不存在")
                return False
            temp_mod_data: dict | None = nosql_data.get(str(key)) # 这里必须进行类型转换才可以设置时间
            if temp_mod_data is None:
                self._e.error("无法获取用户数据，键值: %s", key)
                return False
            if not isinstance(temp_mod_data, dict):
                self._e.error("数据格式错误,期望dict类型,实际类型: %s", type(temp_mod_data))
                return False
            tmp_login_time: str | None = temp_mod_data.get(NosqlEnum.LOGIN_TIME.value) # type: ignore
            temp_mod_data.update(data.info)
            temp_mod_data.update({NosqlEnum.LOGIN_TIME.value: tmp_login_time})
            temp_mod_data.update({NosqlEnum.UPDATE_TIME.value: str(datetime.now().isoformat())})
            return self._write_nosql_data(nosql_data)
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库更新数据失败,失败原因: %s", e)
            return False

    def _update_nosql_data_by_key(self, key: str, field: str, val: str) -> bool:
        try:
            if not key or not field: return False
            nosql_data: dict | None = self._get_nosql_data()
            if nosql_data is None: return False
            if not NosqlEnum.is_in_nosql_field(field):
                self._e.error("修改字段不存在")
                return False
            if field == NosqlEnum.LOGIN_TIME.value:
                self._e.error("登录时间不可修改")
                return False
            tmp_mod_data: dict | None = nosql_data.get(str(key))
            if tmp_mod_data is None:
                self._e.error("用户数据不存在")
                return False
            else:
                tmp_mod_data.update({field: val})
                return self._write_nosql_data(nosql_data)
        except Exception as e:
            self._e.handle_exception(e)
            self._e.error("缓存数据库更新数据失败,失败原因: %s", e)
            return False

class NosqlOperator:
    def __init__(self) -> None:
        raise RuntimeError("操作类不允许通过构造器实例化")

    @classmethod
    def create(cls) -> 'NosqlOperator':
        nosql_core: NosqlCore = NosqlCore.get_instance()
        nosql_op: NosqlOperator = cls.__new__(cls)
        nosql_op._nosql_core: NosqlCore = nosql_core # type: ignore
        return nosql_op

    def in_nosql(self, key: str) -> bool:
        if not key: return False
        temp_nosql_data: dict | None = self._nosql_core._get_nosql_data() # type: ignore
        if temp_nosql_data is None: return False
        return str(key) in temp_nosql_data

    def get_auth(self, key: str) -> str | None:
        if not self.in_nosql(key): return None
        tmp_data: dict = self._nosql_core._get_nosql_data() # type: ignore
        return tmp_data.get(str(key)).get("Authorization") # type: ignore

    def get_data_by_auth(self, auth: str) -> dict | None:
        return self._nosql_core._get_nosql_data_by_auth(auth) # type: ignore

    def get_all_nosql_data(self) -> dict | None:
        return self._nosql_core._get_nosql_data() # type: ignore

    def get_some_nosql_data(self, key: str) -> dict | None:
        if not self.in_nosql(key): return None
        tmp_data: dict = self._nosql_core._get_nosql_data() # type: ignore
        if tmp_data is None: return None
        res_data: dict | None = tmp_data.get(str(key))
        if res_data is None: return None
        else: res_data.setdefault("username", key)
        return res_data

    def update(self, key: str, data: MetaUserData) -> bool:
        return self._nosql_core._update_nosql_data(key, data) # type: ignore

    def update_by_key(self, key: str, field: str, val: str) -> bool:
        return self._nosql_core._update_nosql_data_by_key(key, field, val) # type: ignore

    def delete(self, key: str) -> bool:
        return self._nosql_core._delete_nosql_data(key) # type: ignore

    def insert(self, data: UserData) -> bool:
        return self._nosql_core._insert_nosql_data(data) # type: ignore
