from dataclasses import dataclass

@dataclass
class MetaUserData:
    password: str
    Authorization: str
    is_occupancy: bool = False
    login_time: str | None = None
    update_time: str | None = None

    @property
    def info(self) -> dict:
        return self.__dict__.copy()

@dataclass
class UserData:
    '''
    定义插入nosql的数据格式
    {
        "mock_user": {
            "password": "password",
            "Authorization": "Bearer mock_token",
        }
    }
    '''
    username: str
    metadata: MetaUserData

    @property
    def info(self) -> dict:
        return {
            self.username: self.metadata.info
        }

    @property
    def key(self) -> str:
        return self.username
