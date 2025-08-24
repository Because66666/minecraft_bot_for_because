# -*- coding: utf-8 -*-
"""
KOOK API模块

该模块提供KOOK平台的API接口功能，包括消息发送、频道管理等。
支持机器人令牌认证和错误处理。
"""

import os
import requests
from typing import Optional, Dict, Any
from .my_logger import logger
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class KookAPI:
    """KOOK API管理类"""
    
    def __init__(self, token: Optional[str] = None):
        """初始化KOOK API客户端
        
        Args:
            token: KOOK机器人令牌，如果不提供则从环境变量获取
        """
        self.token = token or os.getenv('KOOK')
        if not self.token:
            logger.error('未找到KOOK机器人令牌，请设置KOOK环境变量')
            self.token = None
            self.base_url = 'https://www.kookapp.cn/api/v3'
            self.session = None
            return
        
        self.base_url = 'https://www.kookapp.cn/api/v3'
        self.session = self._create_session()
        
        logger.info('KOOK API客户端初始化成功')
        
    def _create_session(self) -> requests.Session:
        """创建请求会话
        
        Returns:
            配置好的requests会话对象
        """
        session = requests.Session()
        session.headers.update({
            'Authorization': f'Bot {self.token}',
            'Content-Type': 'application/json'
        })
        return session
        
    def send_message(self, target: str, content: str, msg_type: int = 1) -> Optional[str]:
        """发送消息到KOOK频道
        
        Args:
            target: 目标频道ID
            content: 消息内容
            msg_type: 消息类型，默认为1（文本消息）
            
        Returns:
            响应文本，发送失败时返回None
        """
        if not self.token or not self.session:
            logger.error('KOOK API未正确初始化，无法发送消息')
            return None
            
        if not target:
            logger.warning('目标频道ID为空，跳过消息发送')
            return None
            
        if not content:
            logger.warning('消息内容为空，跳过消息发送')
            return None
            
        try:
            response = self.session.post(
                f'{self.base_url}/message/create',
                json={
                    'type': msg_type,
                    'target_id': target,
                    'content': content
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('message', '未知错误')
                logger.error(f"KOOK API错误: {error_msg}")
                return None
                
            logger.info(f'消息发送成功到频道 {target}: {content[:50]}...')
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f'发送KOOK消息失败: {e}')
            return None
        except Exception as e:
            logger.error(f'KOOK API调用异常: {e}')
            return None
    
    def send_notification(self, content: str, channel_id: Optional[str] = None) -> Optional[str]:
        """发送通知消息到默认频道
        
        Args:
            content: 通知内容
            channel_id: 频道ID，如果不提供则使用默认主频道
            
        Returns:
            响应文本，发送失败时返回None
        """
        if not self.token or not self.session:
            logger.error('KOOK API未正确初始化，无法发送通知')
            return None
            
        if not content:
            logger.warning('通知内容为空，跳过发送')
            return None
            
        target_channel = channel_id or os.getenv('KOOK_MAIN_CHANNEL')
        if not target_channel:
            logger.warning('未配置KOOK主频道ID，无法发送通知')
            return None
            
        return self.send_message(target_channel, content)
    
    def get_channel_info(self, channel_id: str) -> Optional[Dict[str, Any]]:
        """获取频道信息
        
        Args:
            channel_id: 频道ID
            
        Returns:
            频道信息字典，获取失败时返回None
        """
        if not self.token or not self.session:
            logger.error('KOOK API未正确初始化，无法获取频道信息')
            return None
            
        if not channel_id:
            logger.warning('频道ID为空，无法获取频道信息')
            return None
            
        try:
            response = self.session.get(
                f'{self.base_url}/channel/view',
                params={'target_id': channel_id}
            )
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') != 0:
                error_msg = result.get('message', '未知错误')
                logger.error(f"获取频道信息失败: {error_msg}")
                return None
                
            return result.get('data')
            
        except requests.exceptions.RequestException as e:
            logger.error(f'获取频道信息失败: {e}')
            return None
        except Exception as e:
            logger.error(f'KOOK API调用异常: {e}')
            return None
    
    def test_connection(self) -> bool:
        """测试KOOK API连接
        
        Returns:
            连接成功返回True，失败返回False
        """
        if not self.token or not self.session:
            logger.error('KOOK API未正确初始化，无法测试连接')
            return False
            
        try:
            response = self.session.get(f'{self.base_url}/user/me')
            response.raise_for_status()
            result = response.json()
            
            if result.get('code') == 0:
                bot_info = result.get('data', {})
                logger.info(f'KOOK API连接测试成功，机器人: {bot_info.get("username", "未知")}')
                return True
            else:
                logger.error(f'KOOK API连接测试失败: {result.get("message", "未知错误")}')
                return False
                
        except Exception as e:
            logger.error(f'KOOK API连接测试异常: {e}')
            return False


# 全局KOOK API实例
_kook_api_instance = None


def get_kook_api_instance() -> KookAPI:
    """获取KOOK API实例（单例模式）
    
    Returns:
        KOOK API实例
    """
    global _kook_api_instance
    if _kook_api_instance is None:
        try:
            _kook_api_instance = KookAPI()
        except Exception as e:
            logger.error(f'创建KOOK API实例失败: {e}')
            # 创建一个空的实例以避免重复尝试
            _kook_api_instance = KookAPI.__new__(KookAPI)
            _kook_api_instance.token = None
            _kook_api_instance.session = None
            _kook_api_instance.base_url = 'https://www.kookapp.cn/api/v3'
    return _kook_api_instance


def send_kook_message(target: str, content: str, msg_type: int = 1) -> Optional[str]:
    """发送KOOK消息的便捷函数（保持向后兼容）
    
    Args:
        target: 目标频道ID
        content: 消息内容
        msg_type: 消息类型
        
    Returns:
        响应文本，发送失败时返回None
    """
    if not target:
        logger.warning('目标频道ID为空，无法发送KOOK消息')
        return None
        
    if not content:
        logger.warning('消息内容为空，无法发送KOOK消息')
        return None
        
    try:
        kook_api = get_kook_api_instance()
        return kook_api.send_message(target, content, msg_type)
    except Exception as e:
        logger.error(f'发送KOOK消息失败: {e}')
        return None


def send_kook_notification(content: str, channel_id: Optional[str] = None) -> Optional[str]:
    """发送KOOK通知的便捷函数
    
    Args:
        content: 通知内容
        channel_id: 频道ID
        
    Returns:
        响应文本，发送失败时返回None
    """
    if not content:
        logger.warning('通知内容为空，无法发送KOOK通知')
        return None
        
    try:
        kook_api = get_kook_api_instance()
        return kook_api.send_notification(content, channel_id)
    except Exception as e:
        logger.error(f'发送KOOK通知失败: {e}')
        return None