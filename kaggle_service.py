import gradio as gr
import threading
import subprocess
import socket
import logging
import os
import sys
import time
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class S2SService:
    """语音对话服务管理类"""
    def __init__(self):
        self.process = None
        self.status = "停止"
        self.log_queue = []
        self.max_log_lines = 100
        
    def add_log(self, message, level="INFO"):
        """添加日志"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {level}: {message}"
        self.log_queue.append(log_message)
        if len(self.log_queue) > self.max_log_lines:
            self.log_queue.pop(0)
        return "\n".join(self.log_queue)
        
    def check_dependencies(self):
        """检查依赖项"""
        required_files = ["s2s_pipeline.py"]
        missing_files = []
        
        for file in required_files:
            if not Path(file).exists():
                missing_files.append(file)
                
        if missing_files:
            raise FileNotFoundError(f"缺少必要文件: {', '.join(missing_files)}")
            
    def check_ports(self):
        """检查端口占用"""
        for port in [12345, 12346]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('0.0.0.0', port))
                sock.close()
            except socket.error:
                raise RuntimeError(f"端口 {port} 已被占用")
                
    def start_service(self):
        """启动语音对话服务"""
        try:
            # 检查依赖和端口
            self.check_dependencies()
            self.check_ports()
            
            # 构建启动命令
            cmd = [
                sys.executable,
                "s2s_pipeline.py",
                "--recv_host", "0.0.0.0",
                "--send_host", "0.0.0.0",
                "--lm_model_name", "microsoft/Phi-3-mini-4k-instruct",
                "--stt_compile_mode", "reduce-overhead",
                "--tts_compile_mode", "default"
            ]
            
            # 启动进程
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            return self.process
            
        except Exception as e:
            logger.error(f"启动服务失败: {str(e)}")
            raise e
            
    def start(self):
        """启动服务的用户接口"""
        try:
            if self.process is not None:
                return (
                    "服务已在运行中",
                    self.add_log("服务已在运行中", "WARNING")
                )
                
            self.process = self.start_service()
            self.status = "运行中"
            
            # 启动日志监控线程
            def monitor_output():
                while self.process and self.process.poll() is None:
                    # 监控标准输出
                    stdout_line = self.process.stdout.readline()
                    if stdout_line:
                        self.add_log(stdout_line.strip())
                        
                    # 监控错误输出
                    stderr_line = self.process.stderr.readline()
                    if stderr_line:
                        self.add_log(stderr_line.strip(), "ERROR")
                        
            threading.Thread(target=monitor_output, daemon=True).start()
            
            return (
                "服务启动成功",
                self.add_log("服务启动成功")
            )
            
        except Exception as e:
            error_msg = f"启动失败: {str(e)}"
            return (
                error_msg,
                self.add_log(error_msg, "ERROR")
            )
            
    def stop(self):
        """停止服务"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)  # 等待进程终止
                self.process = None
                self.status = "停止"
                return (
                    "服务已停止",
                    self.add_log("服务已停止")
                )
            except subprocess.TimeoutExpired:
                self.process.kill()  # 强制终止
                return (
                    "服务被强制终止",
                    self.add_log("服务被强制终止", "WARNING")
                )
        return (
            "服务未运行",
            self.add_log("服务未运行", "INFO")
        )

def create_ui():
    """创建 Gradio 用户界面"""
    service = S2SService()
    
    with gr.Blocks(title="语音对话服务控制面板") as demo:
        gr.Markdown("""
        # 语音对话服务控制面板
        
        ## 使用说明
        1. 点击"启动服务"按钮启动语音对话服务
        2. 服务启动后，使用提供的公共URL连接客户端
        3. 使用完毕后，点击"停止服务"按钮关闭服务
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                start_btn = gr.Button("启动服务", variant="primary")
                stop_btn = gr.Button("停止服务", variant="stop")
                
            with gr.Column(scale=2):
                status_box = gr.Textbox(
                    label="服务状态",
                    value="未启动",
                    interactive=False
                )
                
        with gr.Row():
            log_box = gr.Textbox(
                label="服务日志",
                value="",
                lines=15,
                max_lines=20,
                interactive=False
            )
            
        # 绑定按钮事件
        start_btn.click(
            fn=service.start,
            outputs=[status_box, log_box]
        )
        
        stop_btn.click(
            fn=service.stop,
            outputs=[status_box, log_box]
        )
        
        # 自动刷新日志
        demo.load(lambda: None, None, log_box, every=5)
        
    return demo

def main():
    """主函数"""
    try:
        demo = create_ui()
        # 启动 Gradio 服务
        demo.launch(
            share=True,          # 创建公共URL
            server_name="0.0.0.0",  # 监听所有网络接口
            server_port=7860,    # Gradio 默认端口
            show_error=True,     # 显示详细错误信息
        )
    except Exception as e:
        logger.error(f"启动 Gradio 服务失败: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 