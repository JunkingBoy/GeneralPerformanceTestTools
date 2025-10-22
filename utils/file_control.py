from pathlib import Path
from datetime import datetime

from utils.logs import ExceptionLog

def create_output_dir(dir_name: str) -> str | None:
    e: ExceptionLog = ExceptionLog.get_instance()
    if not dir_name:
        e.error("创建目录失败：目录名不能为空")
        return
    try:
        parent_dir: Path = Path(__file__).parent.parent / dir_name
        today: str = datetime.now().strftime("%Y%m%d")
        real_dir: Path = parent_dir / today # 类型转换了
        if not real_dir.exists(): real_dir.mkdir(parents=True, exist_ok=True)
        e.info("创建目录成功: %s", real_dir)
        return str(real_dir)
    except Exception as err:
        e.handle_exception(err)
        e.error("创建目录失败: %s", err)
        return
