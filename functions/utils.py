"""工具函数模块

包含各种通用工具函数和错误处理
"""

import re
import os
import sys
import time
import json
import math
import smtplib
import unicodedata
from typing import Dict, List, Optional, Tuple, Any
from email.mime.text import MIMEText
from email.header import Header
from .config import config
from .my_logger import logger


class ValidationError(Exception):
    """验证错误异常"""
    pass


class EmailService:
    """邮件服务类"""
    
    def __init__(self):
        self.mail_config = config.get_mail_config()
    
    def send_verification_code(self, receiver: str, code: str) -> Dict[str, Any]:
        """发送验证码邮件
        
        Args:
            receiver: 接收者邮箱
            code: 验证码
            
        Returns:
            发送结果字典
        """
        if not self.mail_config:
            return {'msg': '邮箱配置错误', 'status': 1}
        
        try:
            # 创建邮件内容
            msg_content = (
                f'你正在登陆Because聊天器，正在请求验证码：{code}。'
                f'如果不是你本人操作，请忽略本次邮件。验证码有效时间5分钟。'
            )
            
            message = MIMEText(msg_content, 'plain', 'utf-8')
            message['From'] = self.mail_config['user']
            message['To'] = receiver
            message['Subject'] = Header('【Because聊天器登陆验证码】', 'utf-8')
            
            # 使用SSL加密方式发送邮件
            smtpObj = smtplib.SMTP_SSL(self.mail_config['host'], self.mail_config['port'])
            # 如果需要验证身份，则取消下面两行的注释，并输入正确的用户名和密码
            smtpObj.login(self.mail_config['user'], self.mail_config['pass'])
            # 发送邮件
            smtpObj.sendmail(self.mail_config['user'], [receiver], message.as_string())
            return {'msg': '验证码发送完成', 'status': 0}
            
        except smtplib.SMTPException as e:
            logger.error(f"发送邮件失败: {e}")
            # logger.error(f"配置信息: {self.mail_config}")
            return {'msg': '验证码发送失败', 'status': 1}
        except Exception as e:
            logger.error(f"邮件服务异常: {e}")
            return {'msg': '邮件服务异常', 'status': 1}


class TextValidator:
    """文本验证器"""
    
    @staticmethod
    def contains_illegal_chars(text: str) -> bool:
        """检查字符串是否包含非法字符
        
        Args:
            text: 要检查的字符串
            
        Returns:
            如果包含非法字符返回True，否则返回False
        """
        # 定义非法字符集
        illegal_chars_pattern = r'[\x00-\x1f\x7f]|§'
        
        # 使用正则表达式检查非法字符
        if re.search(illegal_chars_pattern, text):
            return True
        
        # 检查Unicode类别
        illegal_categories = {'Cc', 'Cf', 'Co', 'Cn'}
        return any(unicodedata.category(c) in illegal_categories for c in text)
    
    @staticmethod
    def validate_message_length(text: str, max_length: int = 90) -> bool:
        """验证消息长度
        
        Args:
            text: 要验证的文本
            max_length: 最大长度
            
        Returns:
            长度是否合法
        """
        return len(text) <= max_length
    
    @staticmethod
    def validate_message(text: str, max_length: int = 90) -> Tuple[bool, str]:
        """验证消息内容
        
        Args:
            text: 要验证的文本
            max_length: 最大长度
            
        Returns:
            (是否有效, 错误信息)
        """
        if TextValidator.contains_illegal_chars(text):
            return False, '禁止特殊字符'
        
        if not TextValidator.validate_message_length(text, max_length):
            return False, '内容过长'
        
        return True, ''


class GeometryUtils:
    """几何计算工具类"""
    
    @staticmethod
    def str_to_tuple(position_str: str) -> Tuple[float, float, float]:
        """将字符串形式的坐标转换为元组形式
        
        Args:
            position_str: 坐标字符串，格式如 "(x, y, z)"
            
        Returns:
            坐标元组 (x, y, z)
        """
        cleaned = position_str.replace("(", "").replace(")", "")
        coords = cleaned.split(",")
        return tuple(map(float, coords))
    
    @staticmethod
    def distance_between_points(point1: Tuple[float, float, float], 
                              point2: Tuple[float, float, float]) -> float:
        """计算两点之间的距离
        
        Args:
            point1: 第一个点的坐标
            point2: 第二个点的坐标
            
        Returns:
            两点之间的距离
        """
        x1, y1, z1 = point1
        x2, y2, z2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)


class FileUtils:
    """文件操作工具类"""
    
    @staticmethod
    def check_player_avatar_exists(player_name: str) -> bool:
        """检查玩家头像文件是否存在
        
        Args:
            player_name: 玩家名字
            
        Returns:
            头像文件是否存在
        """
        avatar_path = os.path.join(config.STATIC_IMG_PATH, f'{player_name}.png')
        return os.path.exists(avatar_path)
    
    @staticmethod
    def get_player_avatar_path(player_name: str) -> str:
        """获取玩家头像路径
        
        Args:
            player_name: 玩家名字
            
        Returns:
            头像文件路径
        """
        if FileUtils.check_player_avatar_exists(player_name):
            return f'{player_name}.png'
        return 'default.jpg'


class EasterEggManager:
    """彩蛋管理器"""
    
    def __init__(self, eggs_file_path: str = None):
        self.eggs_file_path = eggs_file_path or config.EGGS_FILE_PATH
        self.eggs = self._load_eggs()
    
    def _load_eggs(self) -> List[Dict[str, Any]]:
        """加载彩蛋数据
        
        Returns:
            彩蛋列表
        """
        try:
            if os.path.exists(self.eggs_file_path):
                with open(self.eggs_file_path, 'r', encoding='utf8') as f:
                    return json.loads(f.read())
            return []
        except Exception as e:
            logger.error(f"加载彩蛋文件失败: {e}")
            return []
    
    def _save_eggs(self) -> None:
        """保存彩蛋数据到文件"""
        try:
            with open(self.eggs_file_path, 'w', encoding='utf8') as f:
                f.write(json.dumps(self.eggs, ensure_ascii=False, indent=2))
        except Exception as e:
            logger.error(f"保存彩蛋文件失败: {e}")
    
    def check_easter_egg(self, message: str) -> Optional[Dict[str, Any]]:
        """检查消息是否触发彩蛋
        
        Args:
            message: 要检查的消息
            
        Returns:
            如果触发彩蛋返回彩蛋信息，否则返回None
        """
        current_time = int(time.time())
        
        # 清理过期的彩蛋
        self.eggs = [egg for egg in self.eggs if egg.get('end_time', 0) >= current_time]
        
        # 检查是否触发彩蛋
        for egg in self.eggs[:]:
            if egg.get('egg', '') in message:
                self.eggs.remove(egg)
                self._save_eggs()
                return egg
        
        # 如果有彩蛋被清理，保存文件
        if len([egg for egg in self.eggs if egg.get('end_time', 0) >= current_time]) != len(self.eggs):
            self._save_eggs()
        
        return None
    
    def add_easter_egg(self, keyword: str, value: int, duration_minutes: int = 60) -> None:
        """添加新的彩蛋
        
        Args:
            keyword: 彩蛋关键词
            value: 彩蛋价值
            duration_minutes: 有效时长（分钟）
        """
        end_time = int(time.time()) + (duration_minutes * 60)
        egg = {
            'egg': keyword,
            'end_time': end_time,
            'value': value
        }
        self.eggs.append(egg)
        self._save_eggs()
    
    def check(self, message: str) -> Optional[Dict[str, Any]]:
        """检查消息是否触发彩蛋（check_easter_egg的别名）
        
        Args:
            message: 要检查的消息
            
        Returns:
            如果触发彩蛋返回彩蛋信息，否则返回None
        """
        return self.check_easter_egg(message)


class MessageSplitter:
    """消息分割器"""
    
    @staticmethod
    def split_long_message(message: str, chunk_size: int = 90) -> List[str]:
        """分割长消息
        
        Args:
            message: 要分割的消息
            chunk_size: 每段的最大长度
            
        Returns:
            分割后的消息列表
        """
        lines = message.split('\n')
        result = []
        
        for line in lines:
            if len(line) <= chunk_size:
                result.append(line)
            else:
                # 分割长行
                chunks = [line[i:i + chunk_size] for i in range(0, len(line), chunk_size)]
                result.extend(chunks)
        
        return result


class SystemUtils:
    """系统工具类"""
    
    @staticmethod
    def safe_exit(error_info: str, cleanup_functions: List[callable] = None) -> None:
        """安全退出程序
        
        Args:
            error_info: 错误信息
            cleanup_functions: 清理函数列表
        """
        logger.error(f'程序结束，原因：{error_info}')
        
        # 执行清理函数
        if cleanup_functions:
            for cleanup_func in cleanup_functions:
                try:
                    cleanup_func()
                except Exception as e:
                    logger.error(f"执行清理函数失败: {e}")
        
        sys.exit(1)
    @staticmethod
    def check_player_exist(playername: str) -> bool:
        """
        检查这个玩家是否是服务器内玩家，通过名称检查。
        
        Args:
            playername: 玩家名称
            
        Returns:
            bool: 玩家是否存在
        """
        return os.path.exists(f'./static/img/{playername}.png')

    @staticmethod
    def check_email_valid(username:str,email: str) -> bool:
        """
        检查这个邮箱是否是已经绑定的用户，通过邮箱检查。
        
        Args:
            username: 用户名
            email: 邮箱
            
        Returns:
            bool: 邮箱合理
        """
        from database import DatabaseManager, RIAPlayers
        db_manager = DatabaseManager()
        user = db_manager.session.query(RIAPlayers).filter_by(player_name=username).first()
        if user is None:
            return True
        else:
            return user.email == email



# 创建全局实例
email_service = EmailService()
text_validator = TextValidator()
easter_egg_manager = EasterEggManager()
message_splitter = MessageSplitter()