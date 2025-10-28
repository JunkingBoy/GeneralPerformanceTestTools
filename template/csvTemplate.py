from dataclasses import dataclass

@dataclass
class CsvData:
    phone: str
    password: str

    @property
    def info(self) -> dict:
        return self.__dict__.copy()