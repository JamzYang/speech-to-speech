import threading
import queue
import time
import logging
from typing import Optional

class BaseMockHandler:
    def __init__(
        self,
        stop_event: threading.Event,
        queue_in: Optional[queue.Queue] = None,
        queue_out: Optional[queue.Queue] = None,
        name: str = "MockHandler"
    ):
        self.stop_event = stop_event
        self.queue_in = queue_in
        self.queue_out = queue_out
        self.name = name
        self.logger = logging.getLogger(name)

    def run(self):
        self.logger.info(f"{self.name} 启动")
        while not self.stop_event.is_set():
            time.sleep(2)  # 模拟处理时间
            self.logger.info(f"{self.name} 正在运行...") 