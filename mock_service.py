import logging
import time

def mock_service(log_queue):
    """模拟服务运行并产生日志"""
    logger = logging.getLogger('mock.service')
    logger.setLevel(logging.INFO)
    
    while True:
        logger.info("Receiver waiting to be connected...")
        time.sleep(2)
        logger.info("Sender waiting to be connected...")
        time.sleep(2)
        logger.info("Processing some data...")
        time.sleep(3) 