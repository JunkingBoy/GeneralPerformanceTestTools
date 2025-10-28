from dataclasses import dataclass

from enums.errEnum import eEnum

@dataclass
class LogData:
    '''
    设置专门的数据类.用于传递数据到错误处理类中
    '''
    code: int | eEnum
    message: str

    @property
    def info(self) -> dict:
        return self.__dict__.copy()

    def __post_init__(self) -> None:
        if isinstance(self.code, eEnum):
            self.message: str = self.code.err_message
            self.code = int(self.code.err_code)
