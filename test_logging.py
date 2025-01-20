import logging
import queue
import threading
import time
import gradio as gr

# 创建全局日志队列
log_queue = queue.Queue()

# 创建自定义的日志处理器
class QueueHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        try:
            msg = self.format(record)
            self.queue.put(msg)
        except Exception:
            self.handleError(record)

# 模拟服务运行并产生日志
def mock_service(log_queue):
    logger = logging.getLogger('mock.service')
    while True:
        logger.info("Receiver waiting to be connected...")
        time.sleep(2)
        logger.info("Sender waiting to be connected...")
        time.sleep(2)
        logger.info("Processing some data...")
        time.sleep(3)

def setup_logging():
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    
    # 配置队列处理器
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    
    # 配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(queue_handler)
    root_logger.addHandler(console_handler)
    
    logging.info("日志系统初始化完成")

def update_logs():
    logs = []
    while not log_queue.empty():
        try:
            log = log_queue.get_nowait()
            logs.append(log)
        except queue.Empty:
            break
    
    if logs:
        return "\n".join(logs)
    return gr.update()

def run_service():
    setup_logging()
    
    with gr.Blocks() as demo:
        gr.Markdown("## 测试服务已启动")
        gr.Markdown("这是一个测试日志输出的演示")
        
        status = gr.Textbox(label="服务状态", value="运行中")
        logs = gr.Textbox(
            label="服务日志",
            value="初始化中...\n",
            lines=10,
            max_lines=100,
            autoscroll=True
        )
        
        update_btn = gr.Button(visible=False)
        update_btn.click(fn=update_logs, inputs=None, outputs=logs)
        
        demo.load(js="""
            function() {
                setInterval(function(){
                    const btn = document.querySelector('button');
                    if(btn) btn.click();
                }, 500);
            }
        """)
        
        # 启动模拟服务线程
        service_thread = threading.Thread(target=lambda: mock_service(log_queue))
        service_thread.daemon = True
        service_thread.start()
        
        logging.info("模拟服务线程已启动")
    
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0")

if __name__ == "__main__":
    run_service() 