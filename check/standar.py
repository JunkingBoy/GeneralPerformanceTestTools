from requests import Response

from utils.logs import ExceptionLog
from template.httpTemplate import StandardReqDataTemplate
from template.nosqlTemplate import UserData, MetaUserData
from enums.loglabelEnum import LogLabelEnum
from enums.serverEnum import ServerEnum

def standard_normal_check(
    real_resp: Response,
    parse_resp: dict | str | None,
    data: StandardReqDataTemplate
) -> UserData | None:
    e: ExceptionLog = ExceptionLog.get_instance()
    if not isinstance(real_resp, Response):
        e.info("%s 真实响应类型错误,响应类型为: %s", LogLabelEnum.ERROR.value, type(real_resp))
        return
    if not isinstance(data, StandardReqDataTemplate):
        e.info("%s 请求参数类型错误,传入类型为: %s", LogLabelEnum.ERROR.value, type(data))
        return
    if real_resp.status_code != 200:
        e.error("%s 请求失败,服务端状态码: %s", LogLabelEnum.ERROR.value, real_resp.status_code)
        return
    if parse_resp is None:
        e.error("%s 解析响应信息失败", LogLabelEnum.ERROR.value)
        return
    # 响应解析
    match parse_resp:
        case dict() as resp:
            res_code: int = resp.get("code", 0)
            if res_code != ServerEnum.SUCCESS.value:
                e.error("%s 登录失败,服务端状态码: %s, 响应数据: %s", LogLabelEnum.ERROR.value, res_code, parse_resp)
                return
            e.info("%s 用户登录成功", LogLabelEnum.SUCCESS.value)
            auth: str = resp.get("data", {}).get("token")
            username: str = data.body.get("phone") # type: ignore
            password: str = data.body.get("password") # type: ignore
            if not auth:
                e.info("%s 用户登录成功,获取token失败", LogLabelEnum.INFO.value)
                return
            ins_data: UserData = UserData(
                username=username,
                metadata=MetaUserData(
                    password=password,
                    Authorization=auth
                )
            )
            return ins_data
        case str() as resp:
            e.info("%s 响应数据类型解析失败,响应数据类型为: %s, 响应数据为: %s", LogLabelEnum.ERROR.value, type(parse_resp), parse_resp)
            return
        case _:
            e.error("%s 响应数据类型错误,响应数据类型为: %s", LogLabelEnum.ERROR.value, type(parse_resp))
            return
