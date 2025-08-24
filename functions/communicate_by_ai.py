# -*- coding: utf-8 -*-
"""
AI聊天模块 - 基于智谱AI API

该模块提供AI聊天功能，使用智谱AI的GLM模型进行对话。
支持多用户会话管理和上下文记忆。
"""

import os
import time
from typing import Dict, List, Tuple, Any
from zhipuai import ZhipuAI
from dotenv import load_dotenv
from .my_logger import logger

# 加载环境变量
load_dotenv()



class ZhipuAIChat:
    """智谱AI聊天管理类"""
    
    def __init__(self):
        """初始化智谱AI客户端"""
        self.api_key = os.getenv('ZHIPU_AI_API_KEY')
        if not self.api_key:
            logger.error('未找到ZHIPU_AI_API_KEY环境变量，AI功能将不可用')
            self.client = None
            self.model = None
            self.session_timeout = 180
            self.system_prompt = ''
            return
        
        try:
            self.client = ZhipuAI(api_key=self.api_key)
            self.model = os.getenv('ZHIPU_AI_MODEL', 'glm-4-flash')  # 默认使用免费模型
            self.session_timeout = int(os.getenv('AI_SESSION_TIMEOUT', '180'))  # 会话超时时间
            self.system_prompt = os.getenv("SYSTEM_PROMPT",'') # 系统提示词
            
            logger.info(f'智谱AI客户端初始化成功，使用模型: {self.model}')
        except Exception as e:
            logger.error(f'智谱AI客户端初始化失败: {e}')
            self.client = None
            self.model = None
            self.session_timeout = 180
            self.system_prompt = ''
    
    def update_cache(self, messages: List[Dict[str, str]], username: str, cache: Dict[str, Any]) -> Dict[str, Any]:
        """更新用户会话缓存
        
        Args:
            messages: 消息列表
            username: 用户名
            cache: 缓存字典
            
        Returns:
            更新后的缓存字典
        """
        try:
            cache[username]['messages'] = messages
            cache[username]['timestamps'] = int(time.time())
            return cache
        except Exception as e:
            logger.error(f'更新缓存失败: {e}')
            return cache

    def get_messages_by_user(self, user_name: str, cache: Dict[str, Any]) -> Tuple[List[Dict[str, str]], Dict[str, Any]]:
        """获取用户的历史消息
        
        Args:
            user_name: 用户名
            cache: 缓存字典
            
        Returns:
            (历史消息列表, 更新后的缓存)
        """
        try:
            current_time = time.time()
            
            if user_name in cache:
                if current_time - cache[user_name]["timestamps"] < self.session_timeout:
                    # 会话未过期
                    return cache[user_name]["messages"], cache
                else:
                    # 会话过期，重新刷新
                    logger.info(f'用户 {user_name} 的会话已过期，重新初始化')
                    cache[user_name]["messages"] = []
                    cache[user_name]['timestamps'] = int(current_time)
                    return cache[user_name]["messages"], cache
            else:
                # 第一次初始化用户
                logger.info(f'初始化用户 {user_name} 的会话')
                cache[user_name] = {"messages": [], "timestamps": int(current_time)}
                return cache[user_name]["messages"], cache
                
        except Exception as e:
            logger.error(f'获取用户消息失败: {e}')
            # 返回空消息和原缓存
            return [], cache




    def chat(self, username: str, ask_questions: str, caches: Dict[str, Any], reference: Dict[str, str] = None) -> Tuple[str, Dict[str, Any]]:
        """进行AI对话
        
        Args:
            username: 用户名
            ask_questions: 用户问题
            caches: 会话缓存
            reference: 参考内容字典
            
        Returns:
            (AI回复, 更新后的缓存)
        """
        # 检查AI客户端是否正确初始化
        if not self.client:
            logger.error('AI客户端未正确初始化，无法进行对话')
            return '抱歉，AI服务暂时不可用，请检查配置。', caches
            
        # 验证必要参数
        if not username:
            logger.warning('用户名为空，无法进行AI对话')
            return '抱歉，用户信息缺失，无法进行对话。', caches
            
        if not ask_questions:
            logger.warning('用户问题为空，无法进行AI对话')
            return '请输入您的问题。', caches
            
        if caches is None:
            logger.warning('缓存对象为空，使用默认缓存')
            caches = {}
            
        try:
            start_time = time.time()
            
            # 获取历史消息
            messages, cache_2 = self.get_messages_by_user(username, caches)
            
            # 如果有参考内容且是首次对话，添加参考内容
            if reference and len(messages) == 0:
                reference_text = '参考内容：\n'
                for k, v in reference.items():
                    reference_text += f'{k}: {v}\n'
                ask_questions = reference_text + ask_questions
            
            # 添加用户消息
            messages.append({
                "role": "user",
                "content": ask_questions
            })
            
            # 构建完整的消息列表，包含系统提示
            full_messages = [
                {"role": "system", "content": self.system_prompt}
            ] + messages
            
            # 调用智谱AI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=full_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            # 计算响应时间
            elapsed_time = time.time() - start_time
            logger.info(f'AI响应耗时: {elapsed_time:.2f}s')
            
            # 提取回复内容
            if response.choices and len(response.choices) > 0:
                answer = response.choices[0].message.content
                
                # 添加助手回复到消息历史
                messages.append({
                    "role": "assistant",
                    "content": answer
                })
                
                # 更新缓存
                cache_3 = self.update_cache(messages, username, cache_2)
                
                logger.info(f'用户 {username} 的AI对话成功')
                return answer, cache_3
            else:
                logger.error('智谱AI返回空响应')
                return '抱歉，我无法回答您的问题。', cache_2
                
        except Exception as e:
            logger.error(f'AI对话失败: {e}')
            # 清理出错用户的缓存
            if username in caches:
                del caches[username]
            return '抱歉，我无法回答您的问题，请稍后再试。', caches


# 全局AI聊天实例
_ai_chat_instance = None


def get_ai_chat_instance() -> ZhipuAIChat:
    """获取AI聊天实例（单例模式）"""
    global _ai_chat_instance
    if _ai_chat_instance is None:
        try:
            _ai_chat_instance = ZhipuAIChat()
        except Exception as e:
            logger.error(f'创建AI聊天实例失败: {e}')
            # 创建一个空的实例以避免重复尝试
            _ai_chat_instance = ZhipuAIChat.__new__(ZhipuAIChat)
            _ai_chat_instance.client = None
            _ai_chat_instance.model = None
            _ai_chat_instance.session_timeout = 180
            _ai_chat_instance.system_prompt = ''
    return _ai_chat_instance


def main_ai(username: str, ask_questions: str, caches: Dict[str, Any], token: str = None, reference: Dict[str, str] = None) -> Tuple[str, Dict[str, Any]]:
    """主要的AI对话函数（保持向后兼容）
    
    Args:
        username: 用户名
        ask_questions: 用户问题
        caches: 会话缓存
        token: 已废弃，保持兼容性
        reference: 参考内容字典
        
    Returns:
        (AI回复, 更新后的缓存)
    """
    # 验证必要参数
    if not username:
        logger.warning('main_ai: 用户名为空')
        return '抱歉，用户信息缺失。', caches or {}
        
    if not ask_questions:
        logger.warning('main_ai: 用户问题为空')
        return '请输入您的问题。', caches or {}
        
    if caches is None:
        logger.warning('main_ai: 缓存对象为空，使用默认缓存')
        caches = {}
        
    try:
        ai_chat = get_ai_chat_instance()
        return ai_chat.chat(username, ask_questions, caches, reference)
    except Exception as e:
        logger.error(f'AI对话主函数失败: {e}')
        return '抱歉，AI服务暂时不可用。', caches


