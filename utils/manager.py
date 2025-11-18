import time
import copy
import random
import gevent.lock

from gevent.lock import Semaphore
from typing import Optional
from datetime import datetime

from enums.nosqlEnum import NosqlEnum
from enums.loglabelEnum import LogLabelEnum
from template.nosqlTemplate import MetaUserData
from utils.logs import ExceptionLog
from utils.nosql import NosqlOperator

class TokenPool:
    __instance: Optional['TokenPool'] = None
    __lock: Semaphore = gevent.lock.Semaphore()

    @staticmethod
    def get_instance() -> 'TokenPool':
        if TokenPool.__instance: return TokenPool.__instance
        else:
            with TokenPool.__lock:
                if not TokenPool.__instance: TokenPool.__instance = TokenPool()
            return TokenPool.__instance

    def __init__(
        self,
        e: ExceptionLog = ExceptionLog.get_instance(),
        nosql: NosqlOperator = NosqlOperator.create()
    ) -> None:
        if hasattr(self, "__initialized") and self.__initialized:
            return
        else:
            self._e: ExceptionLog = e
            self._nosql: NosqlOperator = nosql
            self._active_pool: set = set()
            self._max_wait_seconds: int = 10
            self.__initialized: bool = True

    @property
    def pool(self) -> set:
        return copy.deepcopy(self._active_pool)

    def _lock_atomic_token(self, username: str) -> bool:
        curr_data: dict | None = self._nosql.get_some_nosql_data(username)
        if curr_data is None:
            self._e.info("缓存数据库无此用户数据,时间: %s", str(datetime.now().isoformat()))
            return False
        if curr_data.get(NosqlEnum.STATUS.value) is False:
            lock_data: MetaUserData = MetaUserData(
                password=curr_data.get(NosqlEnum.PASSWORD.value, ""),
                Authorization=curr_data.get(NosqlEnum.AUTHORIZATION.value, ""),
                is_occupancy=True
            )
            return self._nosql.update(username, lock_data)
        self._e.info("缓存数据库此用户已锁定,时间: %s", str(datetime.now().isoformat()))
        return False

    def _cast_lock_token(self, username: str) -> bool:
        curr_data: dict | None = self._nosql.get_some_nosql_data(username)
        if curr_data is None:
            self._e.info("缓存数据库无此用户数据,时间: %s", str(datetime.now().isoformat()))
            return False
        if curr_data.get(NosqlEnum.STATUS.value) is False:
            self._e.info("缓存数据库此用户未锁定")
            return False
        cast_data: MetaUserData = MetaUserData(
            password=curr_data.get(NosqlEnum.PASSWORD.value, ""),
            Authorization=curr_data.get(NosqlEnum.AUTHORIZATION.value, ""),
            is_occupancy=False
        )
        return self._nosql.update(username, cast_data)

    def _random_token(self) -> tuple | None:
        if not self._active_pool:
            self._e.info("%s 活跃池无数据,请访问缓存数据库", LogLabelEnum.WARNING.value)
            return
        chose_username: str = random.choice(list(self._active_pool))
        lock_token: bool = self._lock_atomic_token(chose_username)
        if not lock_token:
            self._e.error("%s 锁定用户失败,用户ID: %s, 时间: %s", LogLabelEnum.ERROR.value, chose_username, str(datetime.now().isoformat()))
            return
        self._active_pool.discard(chose_username)
        self._e.info("%s 【随机选择】从 %s 个用户中选中成功取出活跃池用户: %s, 池剩余: %s", LogLabelEnum.SUCCESS.value, len(self._active_pool), chose_username, self._active_pool)
        return chose_username, self._nosql.get_auth(chose_username)

    def get_access_token(self, timeout: float = 10.0) -> tuple | None:
        s_time: float = time.time()
        while time.time() - s_time < timeout:
            # 从活跃池中取数据 - 只有一个协程可以从活跃池取数据
            with TokenPool.__lock:
                if self._active_pool:
                    result: tuple | None = self._random_token()
                    if result is not None:
                        user, res = result
                        return user, res
            
            # 池为空 或 抢占失败 → 动态扫描数据库
            all_data: dict | None = self._nosql.get_all_nosql_data()
            if all_data is None:
                self._e.info("缓存数据库无用户数据,时间: %s", str(datetime.now().isoformat()))
                continue # 没到超时时间继续循环

            # 构建活跃池
            candidates: set = set()
            for username, info in all_data.items():
                is_occupancy: bool = info.get(NosqlEnum.STATUS.value)
                token: str = info.get(NosqlEnum.AUTHORIZATION.value)
                if not token:
                    self._e.info("%s 缓存数据库存在脏数据,用户名: %s", LogLabelEnum.ERROR.value, username)
                    continue
                if not is_occupancy:
                    candidates.add(username)

            # 更新原先活跃池 - 只有一个协程可以更新活跃池
            with TokenPool.__lock: self._active_pool = candidates.copy()
            self._e.info("%s 从数据库加载 %d 个空闲用户到活跃池", LogLabelEnum.COUNT_TABLE.value, len(candidates))
            result: tuple | None = self._random_token()
            if result is not None:
                user, res = result
                return user, res
            time.sleep(0.1)
        self._e.error("获取访问令牌超时,时间: %s", str(datetime.now().isoformat()))
        return

    def cast_token(self, username: str) -> None:
        with TokenPool.__lock:
            if not self._cast_lock_token(username):
                self._e.error("%s 释放访问令牌失败,时间: %s", LogLabelEnum.ERROR.value, str(datetime.now().isoformat()))
            else:
                self._active_pool.add(username)
                self._e.info("%s 释放访问令牌成功,时间: %s", LogLabelEnum.SUCCESS.value, str(datetime.now().isoformat()))

    def clear(self) -> None:
        with TokenPool.__lock: self._active_pool.clear()
