import os

from dotenv import load_dotenv

from utils.logs import ExceptionLog

def get_env_var(val: str) -> str:
    load_dotenv()
    e: ExceptionLog = ExceptionLog.get_instance()
    tmp_val: str = val.lower()
    if not tmp_val:
        e.error("获取的环境变量为空,请检查环境变量名称: %s")
        return ""
    return os.getenv(tmp_val, "")
