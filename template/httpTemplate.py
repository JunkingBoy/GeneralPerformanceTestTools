from dataclasses import dataclass

@dataclass
class HttpReqTemplate:
    url: str
    method: str
    params: dict | None
    headers: dict | None
    ssl: bool = False

    @property
    def info(self) -> dict:
        return self.__dict__.copy()
