from enum import Enum

class NosqlEnum(Enum):
    # 定义nosql数据拥有的字段
    PASSWORD = "password"
    AUTHORIZATION = "Authorization"
    STATUS = "is_occupancy"
    LOGIN_TIME = "login_time"
    UPDATE_TIME = "update_time"

    @classmethod
    def is_in_nosql_field(cls, key: str) -> bool:
        for field in cls:
            if field.value == key:
                return True
        return False

    @classmethod
    def get_field_in_nosql(cls, **kwarg) -> list:
        field_list: list = []
        for field in cls:
            if field.value in kwarg: field_list.append(field.value)
        return field_list
