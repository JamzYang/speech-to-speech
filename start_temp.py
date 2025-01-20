import gradio as gr
import threading
import subprocess
from queue import Queue
import time
import logging

def start_s2s_service(log_queue):
    logging.info("正在启动语音服务进程...")
    
    # 启动语音服务进程，并捕获输出
    process = subprocess.Popen([
        "python", "s2s_pipeline.py",
        "--recv_host", "127.0.0.1",
        "--send_host", "127.0.0.1"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
    
    # 读取输出日志的函数
    def read_output(pipe, queue, prefix=''):
        try:
            for line in pipe:
                line = line.strip()
                if line:
                    # 将子进程的输出作为日志记录
                    logging.info(f"{prefix}{line}")
        except Exception as e:
            logging.error(f"读取管道时发生错误: {e}")
    
    # 启动读取输出的线程
    threading.Thread(target=read_output, args=(process.stdout, log_queue, '[s2s] '), daemon=True).start()
    threading.Thread(target=read_output, args=(process.stderr, log_queue, '[s2s][ERROR] '), daemon=True).start()
    
    logging.info("语音服务进程已启动")
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
    
    # 配置日志处理
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # 添加队列处理器
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.handlers = []  # 清除现有处理器
    root_logger.addHandler(console_handler)
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
        update_btn.click(fn=lambda: logs.value = update_logs(), inputs=None, outputs=logs)
        
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