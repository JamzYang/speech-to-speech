import logging
import os
import sys
from pathlib import Path
from queue import Queue
from threading import Event
import gradio as gr

# 添加项目根目录到 Python 路径
CURRENT_DIR = Path(__file__).resolve().parent
if str(CURRENT_DIR) not in sys.path:
    sys.path.append(str(CURRENT_DIR))

from mock.base_handler import BaseMockHandler
from connections.gradio_handler import GradioHandler
from utils.thread_manager import ThreadManager

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

def initialize_queues_and_events():
    return {
        "stop_event": Event(),
        "log_queue": Queue(),
        "mock_queue_1": Queue(),
        "mock_queue_2": Queue(),
        "mock_queue_3": Queue(),
    }

def build_test_pipeline(queues_and_events):
    stop_event = queues_and_events["stop_event"]
    log_queue = queues_and_events["log_queue"]
    
    # 创建处理器链
    handlers = [
        GradioHandler(
            stop_event,
            queue_out=log_queue,
            host="0.0.0.0",
            port=7860
        ),
        BaseMockHandler(
            stop_event,
            queue_in=queues_and_events["mock_queue_1"],
            queue_out=queues_and_events["mock_queue_2"],
            name="MockVAD"
        ),
        BaseMockHandler(
            stop_event,
            queue_in=queues_and_events["mock_queue_2"],
            queue_out=queues_and_events["mock_queue_3"],
            name="MockSTT"
        ),
        BaseMockHandler(
            stop_event,
            queue_in=queues_and_events["mock_queue_3"],
            queue_out=None,
            name="MockTTS"
        ),
    ]
    
    return ThreadManager(handlers)

def main():
    setup_logging()
    logging.info("开始测试 pipeline")
    
    queues_and_events = initialize_queues_and_events()
    pipeline_manager = build_test_pipeline(queues_and_events)

    try:
        pipeline_manager.start()
        # 保持主线程运行
        while not queues_and_events["stop_event"].is_set():
            try:
                queues_and_events["stop_event"].wait(1)
            except KeyboardInterrupt:
                logging.info("收到停止信号")
                queues_and_events["stop_event"].set()
                break
    finally:
        pipeline_manager.stop()
        logging.info("Pipeline 已停止")

if __name__ == "__main__":
    main() 