"""配置管理模块

统一管理应用程序的配置项和环境变量
"""

import os
from dotenv import load_dotenv
from typing import Optional

# 加载环境变量
load_dotenv()


class Config:
    """应用程序配置类"""
    
    # 数据库配置
    DATABASE_URI = 'sqlite:///ria.db'
    CREATIVE_DB_PATH = os.getcwd().replace('mc_bot_2', 'mc_bot/mc.db')
    
    # Flask配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'secret!')
    SQLALCHEMY_DATABASE_URI = 'sqlite:////ria.db'

    # Socket.IO配置
    PING_TIMEOUT = 100
    PING_INTERVAL = 50
    
    # Minecraft服务器配置
    MINECRAFT_HOST = os.getenv('HOST')
    MINECRAFT_PORT = os.getenv('PORT')
    MINECRAFT_USERNAME = os.getenv("PLAYER")
    MINECRAFT_AUTH = os.getenv("AUTH") == 'True'
    SERVER_PASSWORD = os.getenv('SERVER_PASSWORD')
    
    # KOOK配置
    KOOK_TOKEN = os.getenv('KOOK')
    KOOK_BASE_URL = 'https://www.kookapp.cn/api/v3'
    KOOK_MAIN_CHANNEL = os.getenv('KOOK_MAIN_CHANNEL', '')
    KOOK_AI_CHANNEL = os.getenv('KOOK_AI_CHANNEL', '5483801919505226')
    
    # 邮件配置
    MAIL_HOST = os.getenv('MAIL_HOST', 'smtp.qq.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', 465))
    MAIL_USER = os.getenv('MAIL_USER')
    MAIL_PASS = os.getenv('MAIL_PASS')
    
    # 应用配置
    APP_PASSWORD = os.getenv('APP_PASSWORD')
    WELCOME_MESSAGE = '向着星辰与深渊！欢迎来到冒险家协会'
    
    # 文件路径配置
    STATIC_IMG_PATH = './static/img'
    EGGS_FILE_PATH = 'eggs.txt'
    LOGS_DIR = './logs'
    
    @classmethod
    def validate_config(cls) -> bool:
        """验证必要的配置项是否存在
        
        Returns:
            bool: 配置是否有效
        """
        required_configs = [
            cls.MINECRAFT_USERNAME,
            cls.KOOK_TOKEN,
            cls.SECRET_KEY
        ]
        
        missing_configs = []
        for config in required_configs:
            if not config:
                missing_configs.append(config)
        
        if missing_configs:
            print(f"缺少必要配置: {missing_configs}")
            return False
        
        return True
    
    @classmethod
    def get_mail_config(cls) -> Optional[dict]:
        """获取邮件配置
        
        Returns:
            dict: 邮件配置字典，如果配置不完整则返回None
        """
        if not cls.MAIL_USER or not cls.MAIL_PASS:
            return None
        
        return {
            'host': cls.MAIL_HOST,
            'port': cls.MAIL_PORT,
            'user': cls.MAIL_USER,
            'pass': cls.MAIL_PASS
        }


# 创建配置实例
config = Config()