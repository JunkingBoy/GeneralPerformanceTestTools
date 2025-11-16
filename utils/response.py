import json

from requests import Response
from typing import Generic, TypeVar, Union

from enums.loglabelEnum import LogLabelEnum

from utils.logs import ExceptionLog
from utils.file import create_dir

T = TypeVar("T")

class ResponseDiv(Generic[T]):
    '''
    提供校验响应是否是标准三段式的方法
    提供序列化方法
    校验响应结果是否符合请求预期的方法
    '''
    def __init__(
        self,
        data: T,
        e: ExceptionLog = ExceptionLog.get_instance()
    ) -> None:
        self._e: ExceptionLog = e
        if isinstance(data, Response): self._raw_resp: Response = data
        else:
            self._data: T = data
            self._serialize_data: dict | str | None = None

    @staticmethod
    def is_right_serialize(
        data: dict
    ) -> bool:
        if not isinstance(data, dict):
            return False

        required_keys: set = {"code", "message", "data"}
        return required_keys.issubset(data.keys())

    @property
    def data(self) -> T | None:
        if hasattr(self, "_data"): return self._data
        return

    @property
    def serialize(self) -> Union[dict, str, None]:
        if not hasattr(self, "_serialize_data"):
            self._serialize_data = self._try_serialize()
        return self._serialize_data

    def _try_serialize(self) -> Union[dict, str]:
        try:
            json_str: str = json.dumps(
                self._data,
                ensure_ascii=False,
                indent=4
            )
            return json.loads(json_str)
        except Exception as e:
            self._e.handle_exception(e)
            return str(self._data)

    def get_serialize_client_resp(self) -> Union[dict, str, None]:
        if not hasattr(self, "_raw_resp"):
            self._e.info(
                "%s 请求结果类型不正确,实际类型为: %s, 需要类型为: Response",
                LogLabelEnum.WARNING.value,
                type(self._data)
            )
            return
        try:
            resp_data: dict = self._raw_resp.json()
            return resp_data
        except Exception as e:
            self._e.handle_exception(e)
            return self._raw_resp.text
