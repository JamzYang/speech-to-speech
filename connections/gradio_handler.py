import gradio as gr
import logging
import queue
import threading
from typing import Optional
import time

class GradioHandler:
    def __init__(
        self,
        stop_event: threading.Event,
        queue_in: Optional[queue.Queue] = None,  # 可能不需要输入队列
        queue_out: Optional[queue.Queue] = None,  # 用于显示日志
        host: str = "0.0.0.0",
        port: int = 7860,
    ):
        self.stop_event = stop_event
        self.queue_out = queue_out
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        self.ready_event = threading.Event()  # 添加就绪事件

    def update_logs(self):
        logs = []
        while not self.queue_out.empty():
            try:
                log = self.queue_out.get_nowait()
                logs.append(log)
            except queue.Empty:
                break
        
        if logs:
            return "\n".join(logs)
        return gr.update()

    def run(self):
        self.logger.info("启动 Gradio 界面...")
        
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
            update_btn.click(fn=self.update_logs, inputs=None, outputs=logs)
            
            demo.load(js="""
                function() {
                    setInterval(function(){
                        const btn = document.querySelector('button');
                        if(btn) btn.click();
                    }, 500);
                }
            """)

        interface = demo.queue()

        def start_gradio():
            interface.launch(
                server_name=self.host,
                server_port=self.port,
                share=True,
                prevent_thread_lock=True,
                show_api=False,
                quiet=True
            )
            local_url = f"http://{self.host}:{self.port}"
            self.logger.info(f"Gradio 本地访问地址: {local_url}")
            if hasattr(interface, "share_url") and interface.share_url:
                self.logger.info(f"Gradio 公共访问地址: {interface.share_url}")
            self.ready_event.set()  # 标记 Gradio 已就绪

        # 在新线程中启动 Gradio
        gradio_thread = threading.Thread(target=start_gradio)
        gradio_thread.daemon = True
        gradio_thread.start()

        # 等待 Gradio 完全启动
        self.ready_event.wait(timeout=30)  # 设置超时时间为30秒
        self.logger.info("Gradio 界面启动完成")

def build_pipeline(
    module_kwargs,
    socket_receiver_kwargs,
    # ... 其他参数保持不变 ...
    queues_and_events,
):
    stop_event = queues_and_events["stop_event"]
    # ... 其他代码保持不变 ...
    
    # 创建 handlers 列表并添加 GradioHandler
    logger.info("正在初始化 Gradio 界面...")
    gradio_handler = GradioHandler(
        stop_event,
        queue_out=log_queue,
        host="0.0.0.0",
        port=7860
    )
    
    # 直接运行 Gradio（阻塞方式）
    gradio_handler.run()
    logger.info("Gradio 界面初始化完成")
    
    handlers = [gradio_handler]
    
    # 初始化其他组件
    logger.info("正在初始化其他组件...")
    
    # ... 其余代码保持不变 ... 