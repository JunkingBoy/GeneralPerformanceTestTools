from enum import Enum

class CsvMetaEnum(Enum):
    '''
    定义写入csv文件时,csv文件的元数据字段
    '''
    SIG = "signature"
    PUB_ENCRY_KEY = "pubkey_encrypted"

    @classmethod
    def is_valid(cls, name: str) -> bool:
        if not name: return False
        for item in cls:
            if item.value == name: return True
        return False

class CsvHeaderEnum(Enum):
    USERNAME = "username"
    PASSWORD = "password"

    @classmethod
    def get_headers_str(cls) -> str:
        result: list = []
        for item in cls: result.append(item.value)
        return str(result)

    @classmethod
    def get_headers_list(cls) -> list:
        result: list = []
        for item in cls: result.append(item.value)
        return result.copy()

    @classmethod
    def is_headers_str(cls, val: str) -> bool:
        if not val: return False
        if val == CsvHeaderEnum.get_headers_str(): return True
        return False
