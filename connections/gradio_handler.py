import gradio as gr
import logging
import queue
import threading
from typing import Optional

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

        # 使用回调来捕获 Gradio 的 URL 信息
        def log_urls(url, **kwargs):
            self.logger.info(f"Gradio 本地访问地址: {url}")
            if "share_url" in kwargs:
                self.logger.info(f"Gradio 公共访问地址: {kwargs['share_url']}")

        demo.queue()
        demo.launch(
            server_name=self.host,
            server_port=self.port,
            share=True,
            _frontend_reload_interval=False,
            prevent_thread_lock=True,
            show_api=False,
            quiet=True,  # 抑制 Gradio 的默认日志
            callbacks=[log_urls]  # 添加回调来记录 URL
        ) 