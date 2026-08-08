import multiprocessing as mp
import sys
import time
import uuid
import threading
import traceback
import os


def _run_convert(convert_func, src_path, dest_path, password, conn):
    """子进程里的工作函数：捕获 stdout/stderr 写入 Pipe"""
    class PipeWriter:
        """A file-like object that writes to a multiprocessing connection."""
        __slots__ = ("_conn",)
        def __init__(self, conn):
            self._conn = conn
        def write(self, text):
            if text:
                self._conn.send(text)
        def flush(self):
            pass

    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout = PipeWriter(conn)
    sys.stderr = PipeWriter(conn)

    import logging
    root = logging.getLogger()
    formatters = []
    for handler in root.handlers:
        formatters.append(handler.formatter)
        root.removeHandler(handler)
    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(formatters[0] if formatters else logging.Formatter())
    root.addHandler(handler)

    try:
        convert_func(src_path, dest_path, password)
    except Exception:
        traceback.print_exc()   # 会写入 conn
        raise
    finally:
        sys.stdout = old_out
        sys.stderr = old_err
        conn.close()


class PDFConvertManager:
    def __init__(self, convert_func, max_concurrency=None):
        self._convert_func = convert_func
        self._max_concurrency = max_concurrency or os.cpu_count() or 2
        self._tasks = {}
        self._pending_queue = []
        self._running_count = 0
        self._lock = threading.RLock()

    # ---------- 提交任务 ----------
    def submit(self, src_path, dest_path=None, password=None) -> str:
        """
        提交转换任务

        :param src_path: 源 PDF 文件路径
        :param dest_path: 目标 DOCX 文件路径
        :param password: PDF 文件密码
        :return: 任务ID
        """
        # 生成任务的UUID
        task_id = uuid.uuid4().hex

        # 构造任务
        task = {
            "task_id": task_id,
            "src_path": src_path,
            "dest_path": dest_path,
            "password": password,
            "status": "pending",
            "process": None,
            "log_conn": None,
            "log_lines": [],
            "created_at": time.time(),
            "finished_at": None,
            "exitcode": None,
        }
        # 记录
        with self._lock:
            self._tasks[task_id] = task
            self._pending_queue.append(task_id)
        # 调度
        self._schedule()

        return task_id

    def _schedule(self):
        # 调度下一个任务
        # 警告：绝对不要在锁内调用该函数！！！
        with self._lock:
            # 限制并发
            if self._running_count >= self._max_concurrency:
                return
            # 没有待处理的任务
            if not self._pending_queue:
                return

            # 从队列取出一个 task
            task_id = self._pending_queue.pop(0)
            task = self._tasks.get(task_id)
            if task is None or task["status"] != "pending":
                return

            # 创建进程和管道
            parent_conn, child_conn = mp.Pipe(duplex=False)
            process = mp.Process(
                target=_run_convert,
                args=(self._convert_func,
                    task["src_path"], task["dest_path"], task["password"],
                    child_conn),
                daemon=True
            )
            task["process"] = process
            task["log_conn"] = parent_conn
            task["status"] = "running"
            self._running_count += 1

            process.start()

            # 启动日志读取线程
            threading.Thread(target=self._reader,
                            args=(task_id,), daemon=True).start()


    # ---------- 读取日志并更新状态 ----------
    def _reader(self, task_id):
        # 获取完整的task对象，获取管道
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return
            conn = task["log_conn"]

        try:
            # 主循环：读取管道中的日志信息
            while True:
                try:
                    # 读取一行日志，如果管道关闭则退出循环（阻塞）
                    line = conn.recv()
                except EOFError:
                    break
                # 写入日志列表
                with self._lock:
                    if task_id in self._tasks:
                        self._tasks[task_id]["log_lines"].append(line)
                    else:
                        # 任务已被删除，退出循环
                        break
        finally:
            # 管道关闭 = 子进程结束，更新任务状态
            with self._lock:
                task = self._tasks.get(task_id)
                # 如果任务仍然存在且状态为 running，则更新状态为 success/failed/stopped
                if task is not None and task["status"] == "running":
                    task["process"].join()
                    task["finished_at"] = time.time()
                    self._running_count -= 1
                    task["exitcode"] = task["process"].exitcode
                    if task["exitcode"] == 0:
                        task["status"] = "success"
                    elif task["exitcode"] is not None and task["exitcode"] < 0:
                        task["status"] = "stopped"
                    else:
                        task["status"] = "failed"
                # 否则直接不管
            # 然后关闭管道
            conn.close()
            # 尝试调度下一个任务
            self._schedule()
        return

    # ---------- 查询 ----------
    def get_task(self, task_id, throw=True) -> dict:
        """
        获取任务信息

        :param task_id: 任务ID
        :param throw: 如果任务不存在，是否抛出 KeyError
        :return: 任务信息字典
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                if throw:
                    raise KeyError(task_id)
                else:
                    return None
            return {
                "task_id": task["task_id"],
                "src_path": task["src_path"],
                "dest_path": task["dest_path"],
                "status": task["status"],
                "created_at": task["created_at"],
                "finished_at": task["finished_at"],
                "exitcode": task["exitcode"],
                "log": "".join(task["log_lines"]),
            }

    def get_tasks(self) -> list:
        """
        获取所有任务信息

        :return: 任务信息列表
        """
        with self._lock:
            return [
                {
                    "task_id": t["task_id"],
                    "src_path": t["src_path"],
                    "dest_path": t["dest_path"],
                    "status": t["status"],
                    "created_at": t["created_at"],
                    "finished_at": t["finished_at"],
                    "exitcode": t["exitcode"],
                }
                for t in self._tasks.values()
            ]

    def get_log(self, task_id) -> str:
        """
        获取任务日志

        :param task_id: 任务ID
        :return: 任务日志字符串
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            return "".join(task["log_lines"])

    # ---------- 停止 / 删除 ----------
    def _stop_process(self, process, timeout=3):
        """强制终止一个进程：先终止，再等待，必要时强杀。"""
        if not process.is_alive():
            return
        process.terminate()
        process.join(timeout=timeout)
        if process.is_alive():
            process.kill()
            process.join(timeout=timeout)

    def stop(self, task_id) -> bool:
        """
        停止一个正在运行的任务

        :param task_id: 任务ID
        :return: True表示成功停止，False表示任务不存在或已结束
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None or task["status"] != "running":
                return False
            process = task["process"]

        # 在锁外终止进程，避免阻塞其他线程
        self._stop_process(process)
        finished_at = time.time()

        with self._lock:
            task = self._tasks.get(task_id)
            if task is not None and task["status"] == "running":
                task["status"] = "stopped"
                task["finished_at"] = finished_at
                task["exitcode"] = process.exitcode
                self._running_count -= 1
        # 在锁外尝试调度下一个任务
        self._schedule()

        return True

    def delete(self, task_id):
        """
        删除一个任务（无论是否运行中），会尝试终止进程并清理资源。

        :param task_id: 任务ID
        """
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                raise KeyError(task_id)
            process = task["process"]
            was_running = task["status"] == "running"
            self._tasks.pop(task_id) # 阻止其它线程访问这个任务
            log_conn = task["log_conn"]

        # 锁外终止进程（如果在运行）
        if was_running:
            self._stop_process(process)
            with self._lock:
                self._running_count -= 1
            self._schedule()
        # 关闭管道连接等资源
        log_conn.close()


"""
class PDFConvertManager:
    def __init__(self, convert_func):...
    def submit(self, src_path, dest_path=None, password=None) -> str:...
    def get_task(self, task_id, throw=True) -> dict:...
    def get_tasks(self) -> list[dict]:...
    def get_log(self, task_id) -> str:...
    def stop(self, task_id) -> bool:...
    def delete(self, task_id):...

task(dict):
{
    "task_id": str,
    "src_path": str,
    "dest_path": str | None,
    "status": "pending" | "running" | "success" | "failed" | "stopped",
    "created_at": float,
    "finished_at": float | None,
    "exitcode": int | None,
    "log": str,
}
"""
