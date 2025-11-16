import os

from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from utils.logs import ExceptionLog
from enums.loglabelEnum import LogLabelEnum

def create_dir(
    dir_name: str,
    need_date: bool = True
) -> str | None:
    e: ExceptionLog = ExceptionLog.get_instance()
    if not dir_name:
        e.info("%s 目录名称为空: %s", LogLabelEnum.INFO.value, dir_name)
        return
    try:
        cur_dir: Path = Path.cwd()
        dir_path: Path = cur_dir.joinpath(dir_name)
        if not need_date:
            dir_path.mkdir(parents=True, exist_ok=True)
            e.info("%s 创建目录成功: %s", LogLabelEnum.SUCCESS.value, dir_name)
            return dir_path.as_posix()
        today: str = datetime.now().strftime("%Y%m%d")
        tar_path: Path = dir_path.joinpath(today)
        if not tar_path.exists():
            tar_path.mkdir(parents=True, exist_ok=True)
            e.info("%s 创建目录成功: %s", LogLabelEnum.SUCCESS.value, tar_path.as_posix())
        return tar_path.as_posix()
    except Exception as err:
        e.handle_exception(err)
        e.error("%s 创建目录失败: %s", LogLabelEnum.ERROR.value, dir_name)
        return

def get_env_val(env_key: str = "zt") -> str | None:
    load_dotenv()
    if not env_key: temp_val: str = ""
    else: temp_val: str = env_key.upper()
    match temp_val:
        case "ZT":
            host: str = "LQZENTAOHOST"
            return os.getenv(host, "http://localhost:8000")
        case _:
            return os.getenv(temp_val, "")
