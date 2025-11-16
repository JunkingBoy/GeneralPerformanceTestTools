import copy

from typing import Any
from dataclasses import dataclass, fields

@dataclass
class StandardReqHeaderSetTemplate:
    url: str
    method: str
    params: dict | None
    headers: dict | None
    # ssl: bool = False

    @property
    def info(self) -> dict:
        return copy.deepcopy(self.__dict__)

@dataclass
class StandardReqDataTemplate:
    url: str
    method: str
    params: dict | None
    headers: dict | None
    form: dict | None
    body: dict | None

    @property
    def info(self) -> dict:
        res: dict = copy.deepcopy(self.__dict__)
        if self.form is None:
            res.pop("form", None)
        return res

    def set_attr(
        self,
        attr_name: str,
        attr_val: Any
    ) -> bool:
        dict_attrs_key: set[str] = {
            "headers",
            "params",
            "body"
        }

        field_names: set[str] = set()

        for field in fields(self):
            field_names.add(field.name)
        
        if str(attr_name) not in field_names: setattr(self, str(attr_name), attr_val)
        elif not hasattr(self, str(attr_name)): setattr(self, str(attr_name), attr_val)
        else:
            curr_val: str | dict = getattr(self, str(attr_name))
            if (
                str(attr_name) in dict_attrs_key and
                isinstance(curr_val, dict) and
                isinstance(attr_val, dict)
            ):
                # 重新赋值
                curr_val.clear()
                # 合并键值对
                for k, v in attr_val.items():
                    curr_val.setdefault(k, v)
            else:
                setattr(self, str(attr_name), attr_val)
        return True
