from enum import Enum
from typing import Self

'''
专门的错误枚举类
包括错误的code码和message
'''

class eEnum(Enum):
    OSFAIL = (5001, "操作系统错误")
    IOFAIL = (5002, "IO错误")
    TYPEFAIL = (5003, "类型错误")
    ATTRIBUTEFAIL = (5004, "属性错误")
    CONNECTFAIL = (5005, "连接错误")
    UNKNOWNFAIL = (5006, "未知错误")

    def __init__(
        self: Self,
        err_code: int,
        err_message: str
    ) -> None:
        self.err_code: int = int(err_code)
        self.err_message: str = str(err_message)
