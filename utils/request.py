import copy
import requests

from typing import Union
from requests import Response

from utils.logs import ExceptionLog
from utils.response import ResponseDiv
from enums.loglabelEnum import LogLabelEnum
from template.httpTemplate import StandardReqDataTemplate, StandardReqHeaderSetTemplate

class RequestAction:
    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance()
    ) -> None:
        self._e: ExceptionLog = e

    def request_meta(
        self,
        data: StandardReqDataTemplate,
        is_ssl: bool = False,
    ) -> tuple[Response, Union[dict, str, None], StandardReqDataTemplate] | None:
        '''
        1.仅支持json传参
        '''
        tmp_data: StandardReqDataTemplate = copy.deepcopy(data)
        if not isinstance(tmp_data, StandardReqDataTemplate):
            self._e.error("%s 请求数据类型错误,需要的类型为: %s, 实际的类型为: %s", LogLabelEnum.ERROR.value, "StandardReqDataTemplate", type(data))
            return
        req_kwargs: dict = StandardReqHeaderSetTemplate(
            url=tmp_data.url,
            method=tmp_data.method,
            params=tmp_data.params,
            headers=tmp_data.headers
            # ssl=is_ssl
        ).info
        req_kwargs.update({"json": tmp_data.body})
        with requests.request(**req_kwargs) as resp:
            if resp.encoding is None: resp.encoding = "utf-8"
            resp_serialize: ResponseDiv = ResponseDiv(resp)
            resp_data: Union[dict, str, None] = resp_serialize.get_serialize_client_resp()
            return resp, resp_data, tmp_data
