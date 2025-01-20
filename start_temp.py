import gradio as gr
import threading
import subprocess
from queue import Queue
import time

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
    
    # 创建简单的 Gradio 界面
    with gr.Blocks() as demo:
        gr.Markdown("## 语音对话服务已启动")
        gr.Markdown("服务端口: 12345 (接收语音)")
        gr.Markdown("服务端口: 12346 (发送语音)")
        
        # 添加状态显示
        status = gr.Textbox(label="服务状态", value="运行中")
        # 添加日志显示
        logs = gr.Textbox(label="服务日志", value="", lines=10)
        
        # 在后台线程启动服务
        service_thread = threading.Thread(target=lambda: start_s2s_service(log_queue))
        service_thread.daemon = True
        service_thread.start()
        
        # 定期更新日志
        demo.load(fn=update_logs, inputs=None, outputs=logs).every(1)
    
    # 启动 Gradio 界面
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0")

# 运行服务
if __name__ == "__main__":
    run_service()