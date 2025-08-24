import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('./logs'):
    os.mkdir('./logs')

logger = logging.getLogger('Because_bot_system')
logger.setLevel(logging.INFO)

logger_com = logging.getLogger('ria记录器')
logger_com.setLevel(logging.INFO)

logger_ai = logging.getLogger('ai记录器')
logger_ai.setLevel(logging.INFO)

logger_send = logging.getLogger('发送板记录')
logger_send.setLevel(logging.INFO)

logger_file = RotatingFileHandler('./logs/log.txt', backupCount=10, encoding='utf8')
logger_file.setLevel(logging.INFO)

logger_file2 = RotatingFileHandler('./logs/error.txt', maxBytes=10 * 1024 * 1024, backupCount=10, encoding='utf8')
logger_file2.setLevel(logging.ERROR)

logger_file3 = RotatingFileHandler('./logs/communication.txt', encoding='utf8')
logger_file3.setLevel(logging.INFO)

logger_file4 = RotatingFileHandler('./logs/ai.txt', encoding='utf8')
logger_file4.setLevel(logging.INFO)

logger_file5 = RotatingFileHandler('./logs/sending.txt', encoding='utf8')
logger_file5.setLevel(logging.INFO)

# 创建输出到控制台的handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)  # 设置日志级别

# 定义输出格式
formatter = logging.Formatter('[%(asctime)s][%(name)s][%(levelname)s]:%(message)s')
logger_file.setFormatter(formatter)
logger_file2.setFormatter(formatter)
ch.setFormatter(formatter)

formatter_2 = logging.Formatter('[%(asctime)s]:%(message)s')
logger_file3.setFormatter(formatter_2)
logger_file4.setFormatter(formatter_2)
logger_file5.setFormatter(formatter_2)

#添加到处理器中
logger.addHandler(logger_file)
logger.addHandler(logger_file2)
logger.addHandler(ch)
logger_ai.addHandler(logger_file4)
logger_com.addHandler(logger_file3)
logger_send.addHandler(logger_file5)
