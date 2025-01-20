import gradio as gr
import threading
import subprocess
from queue import Queue
import time
import logging

def start_s2s_service(log_queue):
    # 启动语音服务进程，并捕获输出
    process = subprocess.Popen([
        "python", "s2s_pipeline.py",
        "--recv_host", "127.0.0.1",
        "--send_host", "127.0.0.1"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # 读取输出日志的函数
    def read_output(pipe, queue):
        for line in pipe:
            queue.put(line.strip())
    
    # 启动读取输出的线程
    threading.Thread(target=read_output, args=(process.stdout, log_queue), daemon=True).start()
    threading.Thread(target=read_output, args=(process.stderr, log_queue), daemon=True).start()
    
    return process

# 创建一个自定义的日志处理器
class QueueHandler(logging.Handler):
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        msg = self.format(record)
        self.queue.put(msg)

def run_service():
    log_queue = Queue()
    
    def update_logs():
        logs = []
        while True:
            try:
                # 非阻塞方式获取日志
                while not log_queue.empty():
                    log = log_queue.get_nowait()
                    logs.append(log)
                # 只保留最新的100行日志
                logs = logs[-100:]
                return "\n".join(logs)
            except:
                return "\n".join(logs)
    
    # 配置日志处理
    formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    
    # 添加处理器到根日志记录器
    root_logger = logging.getLogger()
    root_logger.addHandler(queue_handler)
    root_logger.setLevel(logging.INFO)
    
    # 确保 connections 模块的日志也被捕获
    connections_logger = logging.getLogger('connections')
    connections_logger.setLevel(logging.INFO)
    
    # 创建简单的 Gradio 界面
    with gr.Blocks() as demo:
        gr.Markdown("## 语音对话服务已启动")
        gr.Markdown("服务端口: 12345 (接收语音)")
        gr.Markdown("服务端口: 12346 (发送语音)")
        
        # 添加状态显示
        status = gr.Textbox(label="服务状态", value="运行中")
        # 添加日志显示
        logs = gr.Textbox(
            label="服务日志",
            value="",
            lines=10,
            max_lines=100,
            autoscroll=True
        )
        
        # 创建一个隐藏的更新按钮
        update_btn = gr.Button(visible=False)
        update_btn.click(fn=update_logs, inputs=None, outputs=logs)
        
        # 添加自动点击脚本
        demo.load(js="""
            function() {
                setInterval(function(){
                    const btn = document.querySelector('button');
                    if(btn) btn.click();
                }, 500);
            }
        """)
        
        # 在后台线程启动服务
        service_thread = threading.Thread(target=lambda: start_s2s_service(log_queue))
        service_thread.daemon = True
        service_thread.start()
    
    # 启动 Gradio 界面
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0")

# 运行服务
if __name__ == "__main__":
    run_service()