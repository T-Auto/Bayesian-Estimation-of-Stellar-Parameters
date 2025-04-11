import logging
import sys

def setup_logging(level=logging.INFO):
    """配置日志记录."""
    # 移除默认的处理器
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 创建并添加新的处理器
    formatter = logging.Formatter('%(asctime)s - %(processName)s - %(levelname)s - %(message)s')
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)
    logging.info("日志系统已配置。")

# 可以在此处添加更复杂的配置，例如写入文件等。 