import logging
import queue
import threading
import time
import gradio as gr
import sys
from s2s_pipeline import main, parse_arguments  # 导入必要的函数

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

def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    queue_handler = QueueHandler(log_queue)
    queue_handler.setFormatter(formatter)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
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

def run_s2s_pipeline(log_queue):
    # 使用系统参数来初始化 pipeline
    sys.argv = [
        sys.argv[0],  # 保持原始脚本名
        "--recv_host", "0.0.0.0",
        "--send_host", "0.0.0.0"
    ]
    
    try:
        # 直接调用 main 函数
        main()
    except Exception as e:
        logging.error(f"Pipeline 执行出错: {str(e)}")

def run_service():
    setup_logging()
    
    with gr.Blocks() as demo:
        gr.Markdown("## S2S Pipeline 服务监控")
        gr.Markdown("实时查看 s2s_pipeline 服务运行状态")
        
        status = gr.Textbox(label="服务状态", value="运行中")
        logs = gr.Textbox(
            label="服务日志",
            value="初始化中...\n",
            lines=15,
            max_lines=200,
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
        
        # 使用和 test_logging.py 相同的方式启动服务
        pipeline_thread = threading.Thread(target=lambda: run_s2s_pipeline(log_queue))
        pipeline_thread.daemon = True
        pipeline_thread.start()
        
        logging.info("S2S Pipeline 服务已启动")
    
    demo.queue()
    demo.launch(share=True, server_name="0.0.0.0")

if __name__ == "__main__":
    run_service() 